import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.schema.memory import BaseMemory
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory

from .database_service import DatabaseService
from .vector_service import VectorService

logger = logging.getLogger(__name__)

class DatabaseBackedMemory(BaseMemory):
    """Custom memory class that uses DatabaseService for persistence"""
    
    def __init__(self, database_service: DatabaseService, conversation_id: str, max_token_limit: int = 2000):
        super().__init__()
        self._database_service = database_service
        self._conversation_id = conversation_id
        self._max_token_limit = max_token_limit
        self._messages: List[BaseMessage] = []
        self._load_messages()
    
    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages
    
    @property
    def database_service(self) -> DatabaseService:
        return self._database_service
    
    @property
    def conversation_id(self) -> str:
        return self._conversation_id
    
    def _load_messages(self):
        """Load messages from database"""
        try:
            db_messages = self._database_service.get_conversation_messages(self._conversation_id)
            self.messages = []
            
            for msg in db_messages:
                if msg['role'] == 'user':
                    self.messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    self.messages.append(AIMessage(content=msg['content']))
            
            logger.info(f"Loaded {len(self.messages)} messages for conversation {self._conversation_id}")
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
        summary_data = self._database_service.get_conversation_summary(self._conversation_id)
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
                self._database_service.add_message(
                    self._conversation_id, "user", inputs["input"]
                )
            
            if "output" in outputs:
                self._database_service.add_message(
                    self._conversation_id, "assistant", outputs["output"]
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
        
        # Memory cache: conversation_id -> ConversationSummaryBufferMemory
        self.memory_cache = {}
        
        # Initialize Google Generative AI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        # Create the prompt template using only {history} and {input} to be compatible with ConversationChain
        self.prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a helpful and accurate AI assistant. Use the prior conversation history to remain consistent.

Conversation history (summarized as needed):
{history}
""",
            ),
            ("human", "{input}")
        ])
        
        logger.info("ChainService initialized successfully")
    
    def get_or_create_memory_for_conversation(self, conversation_id: str) -> ConversationSummaryBufferMemory:
        """Get or create a ConversationSummaryBufferMemory for a conversation (with caching)."""
        if conversation_id not in self.memory_cache:
            logger.info(f"Creating new ConversationSummaryBufferMemory for conversation {conversation_id}")
            # Use same LLM for summarization; memory_key defaults to "history"
            self.memory_cache[conversation_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000,
                memory_key="history",
                return_messages=False,
            )
        return self.memory_cache[conversation_id]
    
    def invoke_chain(self, conversation_id: str, query: str, persona: Dict, model_name: str = "gemini-1.5-flash") -> Dict:
        """Invoke the conversation chain for a single turn using ConversationChain with CSBM."""
        try:
            import time
            start_time = time.time()
            
            # Create a fresh LLM instance if the model name differs
            llm = self.llm
            try:
                current_model_name = getattr(self.llm, "model_name", getattr(self.llm, "model", None))
            except Exception:
                current_model_name = None
            if model_name and model_name != current_model_name:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=os.getenv("GEMINI_API_KEY"),
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            
            # Get or create memory object from cache
            memory = self.get_or_create_memory_for_conversation(conversation_id)
            
            # Get relevant context from vector service
            rag_context = self._get_relevant_context(conversation_id, query)
            
            # Log context retrieval
            if rag_context:
                logger.info("=" * 80)
                logger.info("RELEVANT CONTEXT RETRIEVED:")
                logger.info("=" * 80)
                logger.info(rag_context)
                logger.info("=" * 80)
            else:
                logger.info("No relevant context found for this query")
            
            # Create ConversationChain with memory and prompt
            conversation_chain = ConversationChain(
                llm=llm,
                prompt=self.prompt_template,
                memory=memory,
                verbose=True,
            )

            # Compose a single input string that includes persona, bot name, and RAG context
            bot_name = persona.get("bot_name", "Assistant")
            persona_desc = persona.get("persona", "helpful AI assistant")
            composed_input = (
                f"Bot name: {bot_name}.\n"
                f"Persona: {persona_desc}.\n"
                f"Relevant context (may be empty):\n{rag_context if rag_context else ''}\n\n"
                f"Current Question: {query}"
            )

            # Invoke the chain with ONLY the new inputs for this turn
            invoke_inputs = {"input": composed_input}

            result = conversation_chain.invoke(invoke_inputs)
            response_text = result.get("response") if isinstance(result, dict) else str(result)

            # Persist this turn's exchange to the database (memory is in-process only)
            try:
                self.database_service.add_message(conversation_id, "user", query)
                self.database_service.add_message(conversation_id, "assistant", response_text)
            except Exception as db_err:
                logger.error(f"Error persisting messages to database: {db_err}")

            # Generate and save conversation summary (persisted summary)
            # Disabled for mini-task to reduce latency and because persistence isn't required
            # self._update_conversation_summary(conversation_id, query, response_text)

            # Update vector service with new messages
            self._update_vector_index(conversation_id, query, response_text)
            
            response_time = time.time() - start_time
            
            return {
                "response": response_text,
                "response_time": response_time,
                "success": True,
                "context_used": bool(rag_context),
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
    
    def validate_api_key(self, model_name: str = "gemini-1.5-flash") -> bool:
        """Validate that the API key is working"""
        try:
            # Create a test LLM instance with the specified model
            test_llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.7,
                max_output_tokens=100
            )
            
            # Test with a simple query
            response = test_llm.invoke("Hello")
            
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
