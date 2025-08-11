import google.generativeai as genai
import logging
import time
from typing import List, Dict, Optional
from pydantic import BaseModel

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
    
    def generate_response(self, messages: List[ChatMessage], persona: Optional[Dict] = None) -> Dict:
        """Generate response using Gemini API"""
        try:
            start_time = time.time()
            
            # Get system prompt
            system_prompt = self.get_system_prompt(persona)
            
            # Format conversation
            conversation = self.format_conversation(messages, persona)
            
            # Start chat with history
            if len(conversation) > 1:
                # Create chat with system prompt
                chat = self.model.start_chat(history=conversation[:-1])
                
                # Send the latest message
                latest_message = conversation[-1]["parts"][0]
                response = chat.send_message(latest_message)
            else:
                # Single message, combine system prompt with user message
                user_message = conversation[0]["parts"][0]
                full_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:"
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
