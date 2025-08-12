import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.schema.memory import BaseMemory
from langchain.chains import ConversationChain

from .database_service import DatabaseService
from .vector_service import VectorService

logger = logging.getLogger(__name__)

class DatabaseBackedMemory(BaseMemory):
    """Custom memory class that uses DatabaseService for persistence"""
    
    def __init__(self, database_service: DatabaseService, conversation_id: str, max_token_limit: int = 2000):
        super().__init__()
        self.database_service = database_service
        self.conversation_id = conversation_id
        self.max_token_limit = max_token_limit
        self.messages: List[BaseMessage] = []
        self._load_messages()
    
    def _load_messages(self):
        """Load messages from database"""
        try:
            db_messages = self.database_service.get_conversation_messages(self.conversation_id)
            self.messages = []
            
            for msg in db_messages:
                if msg['role'] == 'user':
                    self.messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    self.messages.append(AIMessage(content=msg['content']))
            
            logger.info(f"Loaded {len(self.messages)} messages for conversation {self.conversation_id}")
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
            self.messages = []
    
    @property
    def memory_variables(self) -> List[str]:
        """Return the memory variables."""
        return ["chat_history", "summary"]
    
    def load_memory_variables(self, inputs: Dict[str, any]) -> Dict[str, any]:
        """Load memory variables."""
        # Get conversation summary
        summary_data = self.database_service.get_conversation_summary(self.conversation_id)
        summary = summary_data.get('learning_progress', '') if summary_data else ''
        
        # Format chat history
        chat_history = ""
        if self.messages:
            chat_history = "\n".join([
                f"{'Human' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
                for msg in self.messages[-10:]  # Last 10 messages
            ])
        
        return {
            "chat_history": chat_history,
            "summary": summary
        }
    
    def save_context(self, inputs: Dict[str, any], outputs: Dict[str, str]) -> None:
        """Save context from this conversation to memory."""
        # Add new messages to memory
        if "input" in inputs:
            self.messages.append(HumanMessage(content=inputs["input"]))
        
        if "output" in outputs:
            self.messages.append(AIMessage(content=outputs["output"]))
        
        # Save to database
        try:
            if "input" in inputs:
                self.database_service.add_message(
                    self.conversation_id, "user", inputs["input"]
                )
            
            if "output" in outputs:
                self.database_service.add_message(
                    self.conversation_id, "assistant", outputs["output"]
                )
        except Exception as e:
            logger.error(f"Error saving context to database: {e}")
    
    def clear(self) -> None:
        """Clear memory contents."""
        self.messages = []

class ChainService:
    """Service for managing LangChain conversation chains"""
    
    def __init__(self, database_service: DatabaseService, vector_service: VectorService):
        self.database_service = database_service
        self.vector_service = vector_service
        
        # Memory cache: conversation_id -> DatabaseBackedMemory
        self.memory_cache = {}
        
        # Initialize Google Generative AI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        # Create the prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are {bot_name}, a {persona}. Your primary goal is to be helpful and accurate.

Here is a summary of our conversation so far:
{summary}

Here is our recent chat history:
{chat_history}

Here is some relevant context from our previous discussions:
{context}

Current Question: {input}

Please provide a helpful and accurate response based on the context and our conversation history."""),
            ("human", "{input}")
        ])
        
        logger.info("ChainService initialized successfully")
    
    def get_or_create_memory_for_conversation(self, conversation_id: str) -> DatabaseBackedMemory:
        """Get or create a memory object for a conversation (with caching)"""
        if conversation_id not in self.memory_cache:
            logger.info(f"Creating new memory object for conversation {conversation_id}")
            self.memory_cache[conversation_id] = DatabaseBackedMemory(
                self.database_service, conversation_id
            )
        return self.memory_cache[conversation_id]
    
    def invoke_chain(self, conversation_id: str, query: str, persona: Dict, model_name: str = "gemini-2.0-flash-exp") -> Dict:
        """
        Invoke the conversation chain for single turn using LangChain's ConversationChain
        """
        try:
            import time
            start_time = time.time()
            
            # Update model if different
            if model_name != "gemini-2.0-flash-exp":
                self.llm.model = model_name
            
            # Get or create memory object from cache
            memory = self.get_or_create_memory_for_conversation(conversation_id)
            
            # Get relevant context from vector service
            context = self._get_relevant_context(conversation_id, query)
            
            # Log context retrieval
            if context:
                logger.info("=" * 80)
                logger.info("RELEVANT CONTEXT RETRIEVED:")
                logger.info("=" * 80)
                logger.info(context)
                logger.info("=" * 80)
            else:
                logger.info("No relevant context found for this query")
            
            # Create ConversationChain with memory
            conversation_chain = ConversationChain(
                llm=self.llm,
                memory=memory,
                verbose=False  # We'll handle our own logging
            )
            
            # Prepare inputs for the chain
            inputs = {
                "input": query,
                "bot_name": persona.get('bot_name', 'Assistant'),
                "persona": persona.get('persona', 'helpful AI assistant'),
                "context": context
            }
            
            # Log the complete prompt being sent to the LLM
            logger.info("=" * 80)
            logger.info("LLM PROMPT BEING SENT:")
            logger.info("=" * 80)
            
            # Format the prompt for logging
            formatted_prompt = f"""System: You are {inputs['bot_name']}, a {inputs['persona']}. Your primary goal is to be helpful and accurate.

Here is a summary of our conversation so far:
{memory.load_memory_variables({})['summary']}

Here is our recent chat history:
{memory.load_memory_variables({})['chat_history']}

Here is some relevant context from our previous discussions:
{inputs['context']}

Current Question: {inputs['input']}

Please provide a helpful and accurate response based on the context and our conversation history."""
            
            logger.info(formatted_prompt)
            logger.info("=" * 80)
            logger.info(f"Prompt Stats: {len(formatted_prompt)} chars, ~{len(formatted_prompt.split())} words")
            logger.info("=" * 80)
            
            # Invoke the conversation chain (LangChain handles memory automatically)
            response = conversation_chain.predict(input=query)
            
            # Log the LLM response
            logger.info("=" * 80)
            logger.info("LLM RESPONSE:")
            logger.info("=" * 80)
            logger.info(response)
            logger.info("=" * 80)
            
            # Generate and save conversation summary
            self._update_conversation_summary(conversation_id, query, response)
            
            # Update vector service with new messages
            self._update_vector_index(conversation_id, query, response)
            
            response_time = time.time() - start_time
            
            return {
                "response": response,
                "response_time": response_time,
                "success": True,
                "context_used": bool(context),
                "model": model_name
            }
            
        except Exception as e:
            logger.error(f"Error in chain invocation: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "response_time": 0,
                "success": False,
                "error": str(e),
                "context_used": False,
                "model": model_name
            }
    
    def _get_relevant_context(self, conversation_id: str, query: str) -> str:
        """Get relevant context from vector service"""
        try:
            similar_messages = self.vector_service.search_similar_messages(
                conversation_id, query, k=3, min_score=0.3
            )
            
            if not similar_messages:
                return ""
            
            context_parts = []
            for msg in similar_messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content_preview']
                context_parts.append(f"{role}: {content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def _update_vector_index(self, conversation_id: str, user_query: str, assistant_response: str):
        """Update vector index with new messages"""
        try:
            # Get the latest messages from database
            messages = self.database_service.get_conversation_messages(conversation_id)
            
            # Convert to vector service format
            vector_messages = []
            for msg in messages[-2:]:  # Last 2 messages (user query + assistant response)
                vector_messages.append({
                    'id': msg['id'],
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp']
                })
            
            # Add to vector service
            if vector_messages:
                self.vector_service.add_messages(conversation_id, vector_messages)
                
        except Exception as e:
            logger.error(f"Error updating vector index: {e}")
    
    def _update_conversation_summary(self, conversation_id: str, user_query: str, assistant_response: str):
        """Update conversation summary using LLM"""
        try:
            # Get existing summary
            summary_data = self.database_service.get_conversation_summary(conversation_id)
            old_summary = summary_data.get('learning_progress', '') if summary_data else ''
            
            # Create summary update prompt
            summary_prompt = f"""You are tasked with updating a conversation summary. 

Current Summary:
{old_summary if old_summary else "No previous summary available."}

Latest Exchange:
User: {user_query}
Assistant: {assistant_response}

Please create a new, concise summary (under 200 words) that:
1. Integrates the new exchange into the existing summary
2. Maintains the key topics and learning progress
3. Focuses on the most important information
4. Is written in a clear, educational tone

New Summary:"""
            
            # Log the summary generation prompt
            logger.info("=" * 80)
            logger.info("SUMMARY GENERATION PROMPT:")
            logger.info("=" * 80)
            logger.info(summary_prompt)
            logger.info("=" * 80)
            
            # Generate new summary
            summary_response = self.llm.invoke(summary_prompt)
            new_summary = summary_response.content.strip()
            
            # Log the generated summary
            logger.info("=" * 80)
            logger.info("GENERATED SUMMARY:")
            logger.info("=" * 80)
            logger.info(new_summary)
            logger.info("=" * 80)
            
            # Save to database
            self.database_service.update_conversation_summary(
                conversation_id=conversation_id,
                topics=[],  # Could be extracted later if needed
                key_questions=[user_query],  # Add current question
                learning_progress=new_summary
            )
            
            logger.info(f"Summary updated for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error updating conversation summary: {e}")
    
    def validate_api_key(self, model_name: str = "gemini-2.0-flash-exp") -> bool:
        """Validate that the API key is working"""
        try:
            # Temporarily change model if needed
            original_model = self.llm.model
            if model_name != original_model:
                self.llm.model = model_name
            
            # Test with a simple query
            response = self.llm.invoke("Hello")
            
            # Restore original model
            if model_name != original_model:
                self.llm.model = original_model
            
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
