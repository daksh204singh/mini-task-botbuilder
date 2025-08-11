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
    
    def get_relevant_context(self, query: str, conversation_id: Optional[str] = None, k: int = 3) -> str:
        """Retrieve relevant context from vector database using RAG"""
        if not self.vector_service:
            return ""
        
        try:
            # Search for similar messages
            similar_messages = self.vector_service.search_similar_messages(query, conversation_id, k)
            
            if not similar_messages:
                return ""
            
            # Format context for the AI
            context_parts = []
            for msg in similar_messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content_preview']
                context_parts.append(f"{role}: {content}")
            
            context = "\n".join(context_parts)
            logger.info(f"Retrieved {len(similar_messages)} relevant context messages for query: {query[:50]}...")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    def generate_response(self, messages: List[ChatMessage], persona: Optional[Dict] = None, conversation_id: Optional[str] = None) -> Dict:
        """Generate response using Gemini API with RAG context"""
        try:
            start_time = time.time()
            
            # Get system prompt
            system_prompt = self.get_system_prompt(persona)
            
            # Get the latest user message
            latest_message = messages[-1].content if messages else ""
            
            # Retrieve relevant context using RAG
            context = self.get_relevant_context(latest_message, conversation_id, k=3)
            
            # Build the prompt with context
            if context:
                context_prompt = f"\n\nRelevant conversation context:\n{context}\n\nCurrent question: {latest_message}\n\nPlease use the context above to provide a relevant and contextual response."
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
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "response_time": 0,
                "tokens_used": None,
                "success": False,
                "error": str(e)
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
