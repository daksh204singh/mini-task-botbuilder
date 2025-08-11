import sqlite3
import uuid
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
from .vector_service import VectorService

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.init_database()
        
        # Initialize vector service
        try:
            self.vector_service = VectorService()
            logger.info("Vector service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            self.vector_service = None
    
    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        bot_name TEXT NOT NULL,
                        persona TEXT NOT NULL,
                        model TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tokens_used INTEGER DEFAULT 0,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """)
                
                # Create message_embeddings table for future RAG functionality
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS message_embeddings (
                        id TEXT PRIMARY KEY,
                        message_id TEXT NOT NULL,
                        conversation_id TEXT NOT NULL,
                        embedding_data BLOB NOT NULL,
                        content_preview TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (message_id) REFERENCES messages (id),
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_conversation(self, session_id: str, bot_name: str, persona: str, model: str) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations (id, session_id, bot_name, persona, model)
                    VALUES (?, ?, ?, ?, ?)
                """, (conversation_id, session_id, bot_name, persona, model))
                conn.commit()
                logger.info(f"Created conversation {conversation_id} for session {session_id}")
                return conversation_id
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    def add_message(self, conversation_id: str, role: str, content: str, tokens_used: int = 0) -> str:
        """Add a message to a conversation and return its ID"""
        message_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (id, conversation_id, role, content, tokens_used)
                    VALUES (?, ?, ?, ?, ?)
                """, (message_id, conversation_id, role, content, tokens_used))
                
                # Update conversation's updated_at timestamp
                cursor.execute("""
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (conversation_id,))
                
                conn.commit()
                logger.info(f"Added message {message_id} to conversation {conversation_id}")
                
                # Add to vector database if vector service is available
                if self.vector_service:
                    try:
                        message_data = {
                            'id': message_id,
                            'role': role,
                            'content': content,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.vector_service.add_conversation_embeddings(conversation_id, [message_data])
                    except Exception as e:
                        logger.error(f"Failed to add message to vector database: {e}")
                
                return message_id
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, role, content, timestamp, tokens_used
                    FROM messages 
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        "id": row[0],
                        "role": row[1],
                        "content": row[2],
                        "timestamp": row[3],
                        "tokens_used": row[4]
                    })
                
                return messages
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, session_id, bot_name, persona, model, created_at, updated_at
                    FROM conversations 
                    WHERE id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "session_id": row[1],
                        "bot_name": row[2],
                        "persona": row[3],
                        "model": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            raise
    
    def get_session_conversations(self, session_id: str) -> List[Dict]:
        """Get all conversations for a session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, bot_name, persona, model, created_at, updated_at
                    FROM conversations 
                    WHERE session_id = ?
                    ORDER BY updated_at DESC
                """, (session_id,))
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        "id": row[0],
                        "bot_name": row[1],
                        "persona": row[2],
                        "model": row[3],
                        "created_at": row[4],
                        "updated_at": row[5]
                    })
                
                return conversations
        except Exception as e:
            logger.error(f"Failed to get session conversations: {e}")
            raise
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete messages first (due to foreign key constraint)
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                
                # Delete conversation
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                conn.commit()
                logger.info(f"Deleted conversation {conversation_id}")
                
                # Remove from vector database if vector service is available
                if self.vector_service:
                    try:
                        self.vector_service.remove_conversation_embeddings(conversation_id)
                    except Exception as e:
                        logger.error(f"Failed to remove conversation from vector database: {e}")
                
                return True
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise
    
    def get_or_create_session_id(self, session_id: Optional[str] = None) -> str:
        """Generate a new session ID if none provided, or return existing one"""
        if not session_id:
            return str(uuid.uuid4())
        return session_id
    
    def search_similar_messages(self, query: str, conversation_id: Optional[str] = None, k: int = 5) -> List[Dict]:
        """Search for similar messages using vector database"""
        if not self.vector_service:
            return []
        return self.vector_service.search_similar_messages(query, conversation_id, k)
    
    def get_conversation_context(self, conversation_id: str, query: str, k: int = 3) -> List[Dict]:
        """Get relevant context from a specific conversation for a query"""
        if not self.vector_service:
            return []
        return self.vector_service.get_conversation_context(conversation_id, query, k)
    
    def get_vector_stats(self) -> Dict:
        """Get statistics about the vector database"""
        if not self.vector_service:
            return {"error": "Vector service not available"}
        return self.vector_service.get_index_stats()
    
    def get_search_analytics(self) -> Dict:
        """Get analytics about RAG search performance"""
        if not self.vector_service:
            return {"error": "Vector service not available"}
        return self.vector_service.get_search_analytics()
    
    def validate_index(self) -> bool:
        """Validate the RAG index integrity"""
        if not self.vector_service:
            return False
        return self.vector_service.validate_index()
    
    def recover_index(self) -> bool:
        """Recover corrupted RAG index"""
        if not self.vector_service:
            return False
        return self.vector_service.recover_index()
    
    def enhanced_search_similar_messages(self, query: str, conversation_id: Optional[str] = None, k: int = 5, min_score: Optional[float] = None) -> List[Dict]:
        """Enhanced search with configurable similarity threshold"""
        if not self.vector_service:
            return []
        return self.vector_service.search_similar_messages(query, conversation_id, k, min_score)
    
    def get_enhanced_conversation_context(self, conversation_id: str, query: str, k: int = 5, min_score: Optional[float] = None) -> List[Dict]:
        """Get enhanced context from a specific conversation with configurable parameters"""
        if not self.vector_service:
            return []
        return self.vector_service.search_similar_messages(query, conversation_id, k, min_score)
