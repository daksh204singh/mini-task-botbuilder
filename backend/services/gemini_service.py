import google.generativeai as genai
import logging
import time
from typing import List, Dict, Optional
from pydantic import BaseModel
from .vector_service import VectorService

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class GeminiService:
    def __init__(self, api_key: str):
        """Initialize Gemini service with API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.chat_history = []
        
        # Initialize vector service for RAG
        try:
            self.vector_service = VectorService()
            logger.info("Vector service initialized for RAG in Gemini service")
        except Exception as e:
            logger.error(f"Failed to initialize vector service for RAG: {e}")
            self.vector_service = None
        
    def format_conversation(self, messages: List[ChatMessage], persona: Optional[str] = None) -> List[Dict]:
        """Format messages for Gemini API"""
        conversation = []
        
        # Convert messages to Gemini format
        for msg in messages:
            if msg.role == "user":
                conversation.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                conversation.append({"role": "model", "parts": [msg.content]})
        
        return conversation
    
    def get_system_prompt(self, persona: Optional[Dict] = None) -> str:
        """Generate system prompt based on persona"""
        if persona:
            bot_name = persona.get('bot_name', 'Assistant')
            persona_desc = persona.get('persona', 'a helpful assistant')
            return f"You are a tutor named {bot_name}, acting as {persona_desc}. Help the user with their questions. Use markdown formatting for your output."
        return "You are a helpful AI assistant. Use markdown formatting for your output."
    
    def get_relevant_context(self, query: str, conversation_id: Optional[str] = None, k: int = 5) -> str:
        """Enhanced context retrieval with better filtering and formatting"""
        if not self.vector_service:
            return ""
        
        try:
            # Search with lower threshold for more results
            similar_messages = self.vector_service.search_similar_messages(
                query, conversation_id, k=k, min_score=0.2
            )
            
            if not similar_messages:
                return ""
            
            # Sort by relevance and recency
            similar_messages.sort(key=lambda x: (x['score'], x['timestamp']), reverse=True)
            
            # Format context with better structure
            context_parts = []
            for msg in similar_messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content_preview']
                score = msg['score']
                context_parts.append(f"{role} (relevance: {score:.2f}): {content}")
            
            context = "\n".join(context_parts)
            logger.info(f"Retrieved {len(similar_messages)} relevant context messages for query: {query[:50]}...")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    def generate_response(self, messages: List[ChatMessage], persona: Optional[Dict] = None, conversation_id: Optional[str] = None) -> Dict:
        """Enhanced response generation with better RAG integration"""
        try:
            start_time = time.time()
            
            # Get system prompt
            system_prompt = self.get_system_prompt(persona)
            
            # Get the latest user message
            latest_message = messages[-1].content if messages else ""
            
            # Retrieve relevant context using RAG
            context = self.get_relevant_context(latest_message, conversation_id, k=5)
            
            # Build enhanced prompt with context
            if context:
                context_prompt = f"""
Relevant conversation context (use this to provide more contextual and consistent responses):
{context}

Current user question: {latest_message}

Instructions:
1. Use the context above to provide relevant and contextual responses
2. If the context contains relevant information, reference it appropriately
3. Maintain consistency with previous responses in the conversation
4. If no relevant context is found, provide a general helpful response

Please respond:"""
                full_prompt = f"{system_prompt}\n\n{context_prompt}\n\nAssistant:"
            else:
                # No context found, use direct approach
                full_prompt = f"{system_prompt}\n\nUser: {latest_message}\n\nAssistant:"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            response_time = time.time() - start_time
            
            # Extract response text
            response_text = response.text
            
            # Get token usage if available
            tokens_used = None
            if hasattr(response, 'usage_metadata'):
                try:
                    tokens_used = response.usage_metadata.total_token_count
                except:
                    tokens_used = None
            
            return {
                "response": response_text,
                "response_time": response_time,
                "tokens_used": tokens_used,
                "success": True,
                "context_used": bool(context)  # Track if context was used
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "response_time": 0,
                "tokens_used": None,
                "success": False,
                "error": str(e),
                "context_used": False
            }
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is working"""
        try:
            # Try a simple generation to test the API key
            response = self.model.generate_content("Hello")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
