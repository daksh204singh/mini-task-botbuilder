import faiss
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector service with sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        
        # In-memory storage: conversation_id -> {index, metadata}
        self.conversation_indexes = {}
        
        # Initialize sentence transformer model
        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
    
    def add_messages(self, conversation_id: str, messages: List[Dict]) -> bool:
        """
        Add conversation messages to the vector database for a specific conversation
        
        Args:
            conversation_id: ID of the conversation
            messages: List of message dictionaries with 'role', 'content', 'id'
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get or create conversation index
            if conversation_id not in self.conversation_indexes:
                self.conversation_indexes[conversation_id] = {
                    'index': faiss.IndexFlatIP(self.dimension),
                    'metadata': []
                }
            
            conversation_data = self.conversation_indexes[conversation_id]
            
            # Prepare texts for embedding
            texts = []
            message_metadata = []
            
            for message in messages:
                content = message.get('content', '').strip()
                if content:  # Only embed non-empty messages
                    texts.append(content)
                    message_metadata.append({
                        'conversation_id': conversation_id,
                        'message_id': message.get('id'),
                        'role': message.get('role'),
                        'content_preview': content[:200] + '...' if len(content) > 200 else content,
                        'timestamp': message.get('timestamp')
                    })
            
            if not texts:
                logger.warning(f"No valid texts to embed for conversation {conversation_id}")
                return False
            
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Add to conversation-specific FAISS index
            conversation_data['index'].add(embeddings.astype('float32'))
            
            # Add metadata
            conversation_data['metadata'].extend(message_metadata)
            
            logger.info(f"Added {len(texts)} embeddings for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding messages: {e}")
            return False
    
    def search_similar_messages(self, conversation_id: str, query: str, k: int = 5, min_score: float = 0.2) -> List[Dict]:
        """
        Search for similar messages in a specific conversation
        
        Args:
            conversation_id: ID of the conversation to search in
            query: Search query text
            k: Number of results to return
            min_score: Minimum similarity score threshold
        
        Returns:
            List of similar message dictionaries
        """
        try:
            if conversation_id not in self.conversation_indexes:
                logger.warning(f"No index found for conversation {conversation_id}")
                return []
            
            conversation_data = self.conversation_indexes[conversation_id]
            index = conversation_data['index']
            metadata = conversation_data['metadata']
            
            if index.ntotal == 0:
                logger.warning(f"Empty index for conversation {conversation_id}")
                return []
            
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_tensor=False)
            
            # Search
            scores, indices = index.search(query_embedding.astype('float32'), min(k, index.ntotal))
            
            # Filter results by minimum score and format
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= min_score and idx < len(metadata):
                    result = metadata[idx].copy()
                    result['similarity_score'] = float(score)
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar messages for query in conversation {conversation_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar messages: {e}")
            return []
    
    def remove_conversation(self, conversation_id: str) -> bool:
        """
        Remove all data for a specific conversation
        
        Args:
            conversation_id: ID of the conversation to remove
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if conversation_id in self.conversation_indexes:
                del self.conversation_indexes[conversation_id]
                logger.info(f"Removed conversation {conversation_id} from vector service")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing conversation: {e}")
            return False
    
    def get_conversation_stats(self, conversation_id: str) -> Dict:
        """
        Get statistics for a specific conversation
        
        Args:
            conversation_id: ID of the conversation
        
        Returns:
            Dictionary with conversation statistics
        """
        try:
            if conversation_id not in self.conversation_indexes:
                return {"error": "Conversation not found"}
            
            conversation_data = self.conversation_indexes[conversation_id]
            index = conversation_data['index']
            metadata = conversation_data['metadata']
            
            # Count messages by role
            user_messages = len([m for m in metadata if m['role'] == 'user'])
            assistant_messages = len([m for m in metadata if m['role'] == 'assistant'])
            
            return {
                "conversation_id": conversation_id,
                "total_embeddings": index.ntotal,
                "total_messages": len(metadata),
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "index_type": "faiss.IndexFlatIP"
            }
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {"error": str(e)}
    
    def get_all_stats(self) -> Dict:
        """
        Get statistics for all conversations
        
        Returns:
            Dictionary with overall statistics
        """
        try:
            total_conversations = len(self.conversation_indexes)
            total_embeddings = sum(
                data['index'].ntotal for data in self.conversation_indexes.values()
            )
            
            return {
                "total_conversations": total_conversations,
                "total_embeddings": total_embeddings,
                "model_name": self.model_name,
                "embedding_dimension": self.dimension
            }
        except Exception as e:
            logger.error(f"Error getting all stats: {e}")
            return {"error": str(e)}
