import google.generativeai as genai
import logging
import time
from typing import List, Dict, Optional, Tuple
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
    
    def analyze_conversation_topics(self, messages: List[ChatMessage]) -> List[str]:
        """Analyze conversation to extract key topics and themes"""
        if not messages or len(messages) < 2:
            return []
        
        try:
            # Create a summary of the conversation for topic analysis
            conversation_summary = "\n".join([
                f"{msg.role}: {msg.content}" for msg in messages[-10:]  # Last 10 messages
            ])
            
            # Use Gemini to extract topics
            topic_prompt = f"""
Analyze this conversation and extract the main topics, themes, and subjects discussed. 
Focus on educational topics, concepts, and areas of learning.

Conversation:
{conversation_summary}

Extract 3-5 key topics as simple phrases (e.g., "Python programming", "Data structures", "Machine learning basics").
Return only the topics, one per line, no numbering or formatting.
"""
            
            response = self.model.generate_content(topic_prompt)
            topics = [topic.strip() for topic in response.text.split('\n') if topic.strip()]
            
            logger.info(f"Extracted topics: {topics}")
            return topics
            
        except Exception as e:
            logger.error(f"Error analyzing conversation topics: {e}")
            return []
    
    def get_simple_context(self, messages: List[ChatMessage], conversation_id: Optional[str] = None) -> str:
        """Simple context retrieval using last 5 messages"""
        if not messages or len(messages) < 2:
            return ""
        
        try:
            # Get the last 5 messages for context
            recent_messages = messages[-5:] if len(messages) > 5 else messages
            
            # Format the recent conversation context
            context_parts = []
            context_parts.append("**Recent Conversation Context:**")
            
            for msg in recent_messages:
                role = "User" if msg.role == 'user' else "Assistant"
                # Truncate long messages for context
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                context_parts.append(f"• {role}: {content}")
            
            context = "\n".join(context_parts)
            logger.info(f"Retrieved simple context with {len(recent_messages)} recent messages")
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving simple context: {e}")
            return ""
    
    def get_intelligent_context(self, query: str, messages: List[ChatMessage], conversation_id: Optional[str] = None) -> Tuple[str, Dict]:
        """Enhanced context retrieval with intelligent analysis"""
        if not self.vector_service:
            return "", {}
        
        try:
            context_info = {
                "topics_discussed": [],
                "last_questions": [],
                "relevant_context": [],
                "context_strategy": "none"
            }
            
            # Strategy 1: Analyze conversation topics
            if len(messages) > 2:
                topics = self.analyze_conversation_topics(messages)
                context_info["topics_discussed"] = topics
                
                # Search for messages related to these topics using topic-based search
                topic_contexts = self.vector_service.search_by_topics(
                    topics[:3], conversation_id, k=2
                )
                
                if topic_contexts:
                    context_info["context_strategy"] = "topic_based"
                    context_info["relevant_context"] = topic_contexts
            
            # Strategy 2: Get recent questions and answers
            recent_messages = self.vector_service.search_similar_messages(
                query, conversation_id, k=3, min_score=0.25
            )
            
            # Extract last few questions from the conversation
            user_messages = [msg for msg in messages[-6:] if msg.role == 'user']
            if user_messages:
                context_info["last_questions"] = [msg.content for msg in user_messages[-3:]]
            
            # Strategy 3: Direct semantic search for current query
            direct_context = self.vector_service.search_similar_messages(
                query, conversation_id, k=2, min_score=0.4
            )
            
            # Combine all context strategies
            all_context = []
            
            # Add topic-based context
            if context_info["relevant_context"]:
                all_context.extend(context_info["relevant_context"])
            
            # Add direct semantic context
            if direct_context:
                all_context.extend(direct_context)
            
            # Remove duplicates and sort by relevance
            unique_context = {}
            for ctx in all_context:
                key = f"{ctx['role']}_{ctx['content_preview'][:50]}"
                if key not in unique_context or ctx['score'] > unique_context[key]['score']:
                    unique_context[key] = ctx
            
            sorted_context = sorted(unique_context.values(), key=lambda x: x['score'], reverse=True)
            
            # Format the context intelligently
            context_parts = []
            
            # Add conversation summary if we have topics
            if context_info["topics_discussed"]:
                topics_str = ", ".join(context_info["topics_discussed"][:3])
                context_parts.append(f"**Conversation Topics:** {topics_str}")
                context_parts.append("")
            
            # Add recent questions if available
            if context_info["last_questions"]:
                context_parts.append("**Recent Questions:**")
                for i, question in enumerate(context_info["last_questions"][-2:], 1):
                    context_parts.append(f"{i}. {question}")
                context_parts.append("")
            
            # Add relevant context messages
            if sorted_context:
                context_parts.append("**Relevant Context:**")
                for ctx in sorted_context[:4]:  # Limit to 4 most relevant
                    role = "User" if ctx['role'] == 'user' else "Assistant"
                    content = ctx['content_preview']
                    context_parts.append(f"• {role}: {content}")
            
            context = "\n".join(context_parts)
            logger.info(f"Retrieved intelligent context using strategy: {context_info['context_strategy']}")
            
            return context, context_info
            
        except Exception as e:
            logger.error(f"Error retrieving intelligent context: {e}")
            return "", {"context_strategy": "error", "error": str(e)}
    
    def get_relevant_context(self, query: str, conversation_id: Optional[str] = None, k: int = 5) -> str:
        """Legacy method - now uses simple context"""
        return self.get_simple_context([], conversation_id)
    
    def generate_response(self, messages: List[ChatMessage], persona: Optional[Dict] = None, conversation_id: Optional[str] = None) -> Dict:
        """Enhanced response generation with simple but effective context"""
        try:
            start_time = time.time()
            
            # Get system prompt
            system_prompt = self.get_system_prompt(persona)
            
            # Get the latest user message
            latest_message = messages[-1].content if messages else ""
            
            # Get simple context using last 5 messages
            context = self.get_simple_context(messages, conversation_id)
            
            # Build enhanced prompt with context
            if context:
                context_prompt = f"""
{context}

**Current Question:** {latest_message}

**Instructions:**
1. Use the conversation context above to provide relevant and contextual responses
2. Reference previous topics and questions when appropriate
3. Maintain consistency with the conversation flow
4. If the context shows the user is learning about specific topics, tailor your response accordingly
5. Build upon previous explanations and avoid repetition

Please provide a helpful response:"""
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
                "context_used": bool(context),
                "context_info": {"strategy": "simple_context", "messages_used": len(messages[-5:]) if messages else 0}
            }
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "response_time": 0,
                "tokens_used": None,
                "success": False,
                "error": str(e),
                "context_used": False,
                "context_info": {"strategy": "error", "error": str(e)}
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
