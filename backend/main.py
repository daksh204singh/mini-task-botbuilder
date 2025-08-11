from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from services.gemini_service import GeminiService, ChatMessage
from services.database_service import DatabaseService
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini Service
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

try:
    gemini_service = GeminiService(GEMINI_API_KEY)
    if not gemini_service.validate_api_key():
        raise ValueError("Invalid Gemini API key")
    logger.info("Gemini service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini service: {e}")
    raise

# Initialize Database Service
try:
    database_service = DatabaseService()
    logger.info("Database service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database service: {e}")
    raise

app = FastAPI(title="TutorBot API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class Persona(BaseModel):
    bot_name: str
    persona: str
    model: str = "gemini-2.0-flash-exp"

class ChatRequest(BaseModel):
    messages: List[Message]
    persona: Persona
    temperature: Optional[float] = 0.7
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    response_time: float
    tokens_used: Optional[int] = None
    conversation_id: str
    session_id: str
    context_used: Optional[bool] = None

@app.get("/")
async def root():
    return {"message": "TutorBot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "gemini-2.0-flash-exp"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Handle session and conversation management
        session_id = database_service.get_or_create_session_id(request.session_id)
        
        # If no conversation_id provided, create a new conversation
        if not request.conversation_id:
            conversation_id = database_service.create_conversation(
                session_id=session_id,
                bot_name=request.persona.bot_name,
                persona=request.persona.persona,
                model=request.persona.model
            )
        else:
            conversation_id = request.conversation_id
            # Verify conversation exists and belongs to session
            conversation = database_service.get_conversation(conversation_id)
            if not conversation or conversation["session_id"] != session_id:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Store the latest user message in database
        if request.messages:
            latest_message = request.messages[-1]
            database_service.add_message(
                conversation_id=conversation_id,
                role=latest_message.role,
                content=latest_message.content
            )
        
        # Convert request messages to ChatMessage format for Gemini
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content, timestamp=msg.timestamp)
            for msg in request.messages
        ]
        
        # Generate response using Gemini service with RAG
        result = gemini_service.generate_response(
            messages=chat_messages,
            persona=request.persona.dict(),
            conversation_id=conversation_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # Store the assistant response in database
        database_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result["response"],
            tokens_used=result.get("tokens_used", 0)
        )
        
        return ChatResponse(
            response=result["response"],
            model=request.persona.model,
            response_time=result["response_time"],
            tokens_used=result["tokens_used"],
            conversation_id=conversation_id,
            session_id=session_id,
            context_used=result.get("context_used", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.get("/models")
async def get_models():
    """Get available models"""
    return {
        "models": [
            {
                "id": "gemini-2.0-flash-exp",
                "name": "Gemini 2.0 Flash",
                "description": "Latest fast and efficient model for general tasks"
            },
            {
                "id": "gemini-1.5-flash",
                "name": "Gemini 1.5 Flash",
                "description": "Previous generation fast model"
            }
        ]
    }

@app.post("/session")
async def create_session():
    """Create a new session and return session ID"""
    try:
        session_id = database_service.get_or_create_session_id()
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@app.get("/session/{session_id}/conversations")
async def get_session_conversations(session_id: str):
    """Get all conversations for a session"""
    try:
        conversations = database_service.get_session_conversations(session_id)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error getting session conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details and messages"""
    try:
        conversation = database_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = database_service.get_conversation_messages(conversation_id)
        return {
            "conversation": conversation,
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")

@app.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages"""
    try:
        success = database_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.get("/search")
async def search_messages(query: str, conversation_id: Optional[str] = None, k: int = 5):
    """Search for similar messages using vector database"""
    try:
        results = database_service.search_similar_messages(query, conversation_id, k)
        return {"results": results, "query": query, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")

@app.get("/conversation/{conversation_id}/context")
async def get_conversation_context(conversation_id: str, query: str, k: int = 3):
    """Get relevant context from a specific conversation for a query"""
    try:
        # Verify conversation exists
        conversation = database_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        context = database_service.get_conversation_context(conversation_id, query, k)
        return {"context": context, "query": query, "conversation_id": conversation_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting context: {str(e)}")

@app.get("/vector-stats")
async def get_vector_stats():
    """Get statistics about the vector database"""
    try:
        stats = database_service.get_vector_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting vector stats: {str(e)}")

@app.get("/rag/analytics")
async def get_rag_analytics():
    """Get analytics about RAG search performance"""
    try:
        analytics = database_service.get_search_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error getting RAG analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting RAG analytics: {str(e)}")

@app.get("/rag/validate")
async def validate_rag_index():
    """Validate the RAG index integrity"""
    try:
        is_valid = database_service.validate_index()
        return {"valid": is_valid}
    except Exception as e:
        logger.error(f"Error validating RAG index: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating RAG index: {str(e)}")

@app.post("/rag/recover")
async def recover_rag_index():
    """Recover corrupted RAG index"""
    try:
        success = database_service.recover_index()
        return {"success": success, "message": "Index recovery completed" if success else "Index recovery failed"}
    except Exception as e:
        logger.error(f"Error recovering RAG index: {e}")
        raise HTTPException(status_code=500, detail=f"Error recovering RAG index: {str(e)}")

@app.get("/rag/search")
async def enhanced_search(
    query: str, 
    conversation_id: Optional[str] = None, 
    k: int = 5, 
    min_score: Optional[float] = None
):
    """Enhanced search with configurable similarity threshold"""
    try:
        results = database_service.enhanced_search_similar_messages(query, conversation_id, k, min_score)
        return {
            "results": results, 
            "query": query, 
            "count": len(results),
            "min_score_used": min_score or 0.3
        }
    except Exception as e:
        logger.error(f"Error in enhanced search: {e}")
        raise HTTPException(status_code=500, detail=f"Error in enhanced search: {str(e)}")

@app.get("/rag/context")
async def get_enhanced_context(
    conversation_id: str, 
    query: str, 
    k: int = 5,
    min_score: Optional[float] = None
):
    """Get enhanced context from a specific conversation with configurable parameters"""
    try:
        # Verify conversation exists
        conversation = database_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        context = database_service.get_enhanced_conversation_context(conversation_id, query, k, min_score)
        return {
            "context": context, 
            "query": query, 
            "conversation_id": conversation_id,
            "min_score_used": min_score or 0.3
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced context: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting enhanced context: {str(e)}")
