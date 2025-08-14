from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from services.database_service import DatabaseService
from services.vector_service import VectorService
from services.chain_service import ChainService
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
database_service: Optional[DatabaseService] = None
vector_service: Optional[VectorService] = None
chain_service: Optional[ChainService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    global database_service, vector_service, chain_service
    
    # Initialize services
    try:
        logger.info("Initializing services...")
        
        # Initialize Database Service
        database_service = DatabaseService()
        logger.info("Database service initialized")
        
        # Initialize Vector Service
        vector_service = VectorService()
        logger.info("Vector service initialized")
        
        # Initialize Chain Service
        chain_service = ChainService(database_service, vector_service)
        if not chain_service.validate_api_key("gemini-1.5-flash"):
            raise ValueError("Invalid Gemini API key")
        logger.info("Chain service initialized")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Cleanup (if needed)
    logger.info("Shutting down services...")

# Create FastAPI app with lifespan
app = FastAPI(title="TutorBot API", version="2.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://daksh204singh.github.io",  # GitHub Pages
        os.getenv("FRONTEND_URL", "http://localhost:3000")  # Environment variable
    ],
    # Allow all GitHub Pages origins like https://username.github.io
    allow_origin_regex=r"^https:\/\/([A-Za-z0-9-]+)\.github\.io$",
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
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str
    response_time: float
    conversation_id: str
    session_id: str
    context_used: Optional[bool] = None

class ConversationResponse(BaseModel):
    id: str
    bot_name: str
    persona: str
    model: str
    created_at: str
    updated_at: str

class SessionResponse(BaseModel):
    session_id: str

@app.get("/")
async def root():
    return {"message": "TutorBot API v2.0 is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model": "gemini-1.5-flash",
        "services": {
            "database": database_service is not None,
            "vector": vector_service is not None,
            "chain": chain_service is not None
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - simplified to use ChainService"""
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
        
        # Get the latest user message
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        latest_message = request.messages[-1].content
        
        # Invoke the chain service
        result = chain_service.invoke_chain(
            conversation_id=conversation_id,
            query=latest_message,
            persona=request.persona.dict(),
            model_name=request.persona.model
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            response_time=result["response_time"],
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

@app.post("/session", response_model=SessionResponse)
async def create_session():
    """Create a new session and return session ID"""
    try:
        session_id = database_service.get_or_create_session_id()
        return SessionResponse(session_id=session_id)
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

@app.get("/session/{session_id}/conversations", response_model=List[ConversationResponse])
async def get_session_conversations(session_id: str):
    """Get all conversations for a session"""
    try:
        conversations = database_service.get_session_conversations(session_id)
        return [
            ConversationResponse(
                id=conv["id"],
                bot_name=conv["bot_name"],
                persona=conv["persona"],
                model=conv["model"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            )
            for conv in conversations
        ]
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
        # Delete from database
        success = database_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete from vector service
        vector_service.remove_conversation(conversation_id)
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        db_stats = {
            "total_conversations": len(database_service.get_all_conversations())
        }
        
        vector_stats = vector_service.get_all_stats()
        
        return {
            "database": db_stats,
            "vector": vector_stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TutorBot API v2.0 server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
