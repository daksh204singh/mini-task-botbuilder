import sqlite3
import uuid
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.init_database()
    
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
                
                # Create conversation_summaries table for persistent context
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_summaries (
                        conversation_id TEXT PRIMARY KEY,
                        topics TEXT,
                        key_questions TEXT,
                        learning_progress TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                        'id': row[0],
                        'role': row[1],
                        'content': row[2],
                        'timestamp': row[3],
                        'tokens_used': row[4]
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
                        'id': row[0],
                        'session_id': row[1],
                        'bot_name': row[2],
                        'persona': row[3],
                        'model': row[4],
                        'created_at': row[5],
                        'updated_at': row[6]
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
                        'id': row[0],
                        'bot_name': row[1],
                        'persona': row[2],
                        'model': row[3],
                        'created_at': row[4],
                        'updated_at': row[5]
                    })
                
                return conversations
        except Exception as e:
            logger.error(f"Failed to get session conversations: {e}")
            raise
    
    def get_or_create_session_id(self, session_id: Optional[str] = None) -> str:
        """Get existing session ID or create a new one"""
        if session_id:
            return session_id
        return str(uuid.uuid4())
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if conversation exists
                cursor.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
                if not cursor.fetchone():
                    return False
                
                # Delete messages first (due to foreign key constraint)
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
                
                # Delete conversation summary
                cursor.execute("DELETE FROM conversation_summaries WHERE conversation_id = ?", (conversation_id,))
                
                # Delete conversation
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                conn.commit()
                logger.info(f"Deleted conversation {conversation_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            raise
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT topics, key_questions, learning_progress, last_updated
                    FROM conversation_summaries 
                    WHERE conversation_id = ?
                """, (conversation_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'topics': json.loads(row[0]) if row[0] else [],
                        'key_questions': json.loads(row[1]) if row[1] else [],
                        'learning_progress': row[2],
                        'last_updated': row[3]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            raise
    
    def update_conversation_summary(self, conversation_id: str, topics: List[str], 
                                  key_questions: List[str], learning_progress: str) -> bool:
        """Update conversation summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO conversation_summaries 
                    (conversation_id, topics, key_questions, learning_progress, last_updated)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    conversation_id,
                    json.dumps(topics),
                    json.dumps(key_questions),
                    learning_progress
                ))
                conn.commit()
                logger.info(f"Updated summary for conversation {conversation_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update conversation summary: {e}")
            raise
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations (for testing/debugging)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, session_id, bot_name, persona, model, created_at, updated_at
                    FROM conversations 
                    ORDER BY updated_at DESC
                """)
                
                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'id': row[0],
                        'session_id': row[1],
                        'bot_name': row[2],
                        'persona': row[3],
                        'model': row[4],
                        'created_at': row[5],
                        'updated_at': row[6]
                    })
                
                return conversations
        except Exception as e:
            logger.error(f"Failed to get all conversations: {e}")
            raise
