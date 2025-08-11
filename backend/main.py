from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from services.gemini_service import GeminiService, ChatMessage
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

class ChatResponse(BaseModel):
    response: str
    model: str
    response_time: float
    tokens_used: Optional[int] = None

@app.get("/")
async def root():
    return {"message": "TutorBot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "gemini-2.0-flash-exp"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Convert request messages to ChatMessage format
        chat_messages = [
            ChatMessage(role=msg.role, content=msg.content, timestamp=msg.timestamp)
            for msg in request.messages
        ]
        
        # Generate response using Gemini service
        result = gemini_service.generate_response(
            messages=chat_messages,
            persona=request.persona.dict()
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return ChatResponse(
            response=result["response"],
            model=request.persona.model,
            response_time=result["response_time"],
            tokens_used=result["tokens_used"]
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
