import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "conversation_vectors.faiss", metadata_path: str = "vector_metadata.pkl"):
        """
        Initialize the vector service with FAISS index and sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
            index_path: Path to save/load the FAISS index
            metadata_path: Path to save/load vector metadata
        """
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Initialize sentence transformer model
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
        
        # Initialize FAISS index and metadata
        self.index = None
        self.metadata = []
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                # Load existing index
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.metadata = []
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Error loading/creating FAISS index: {e}")
            # Create new index as fallback
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Saved FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def add_conversation_embeddings(self, conversation_id: str, messages: List[Dict]) -> bool:
        """
        Add conversation messages to the vector database
        
        Args:
            conversation_id: ID of the conversation
            messages: List of message dictionaries with 'role', 'content', 'id'
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
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
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Add metadata
            self.metadata.extend(message_metadata)
            
            # Save index
            self._save_index()
            
            logger.info(f"Added {len(texts)} embeddings for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding conversation embeddings: {e}")
            return False
    
    def search_similar_messages(self, query: str, conversation_id: Optional[str] = None, k: int = 5) -> List[Dict]:
        """
        Search for similar messages in the vector database
        
        Args:
            query: Search query text
            conversation_id: Optional conversation ID to filter results
            k: Number of results to return
        
        Returns:
            List of dictionaries with similar messages and their metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_tensor=False)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), min(k * 2, self.index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                if idx < len(self.metadata):
                    metadata = self.metadata[idx]
                    
                    # Filter by conversation_id if specified
                    if conversation_id and metadata['conversation_id'] != conversation_id:
                        continue
                    
                    results.append({
                        'score': float(score),
                        'conversation_id': metadata['conversation_id'],
                        'message_id': metadata['message_id'],
                        'role': metadata['role'],
                        'content_preview': metadata['content_preview'],
                        'timestamp': metadata['timestamp']
                    })
                    
                    if len(results) >= k:
                        break
            
            logger.info(f"Found {len(results)} similar messages for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar messages: {e}")
            return []
    
    def get_conversation_context(self, conversation_id: str, query: str, k: int = 3) -> List[Dict]:
        """
        Get relevant context from a specific conversation for a query
        
        Args:
            conversation_id: ID of the conversation to search in
            query: Search query
            k: Number of context messages to return
        
        Returns:
            List of relevant context messages
        """
        return self.search_similar_messages(query, conversation_id, k)
    
    def remove_conversation_embeddings(self, conversation_id: str) -> bool:
        """
        Remove all embeddings for a specific conversation
        
        Note: FAISS doesn't support direct deletion, so we rebuild the index
        """
        try:
            # Create new index without the conversation
            new_index = faiss.IndexFlatIP(self.dimension)
            new_metadata = []
            
            # Rebuild index excluding the conversation
            for i, metadata in enumerate(self.metadata):
                if metadata['conversation_id'] != conversation_id:
                    # Get the embedding for this metadata
                    embedding = self.index.reconstruct(i)
                    new_index.add(embedding.reshape(1, -1).astype('float32'))
                    new_metadata.append(metadata)
            
            # Replace old index and metadata
            self.index = new_index
            self.metadata = new_metadata
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Removed embeddings for conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing conversation embeddings: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get statistics about the vector database"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'model_name': self.model_name,
            'conversations': len(set(m['conversation_id'] for m in self.metadata)) if self.metadata else 0
        }
