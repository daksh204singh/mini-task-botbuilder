import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", 
                 index_path: str = "conversation_vectors.faiss", 
                 metadata_path: str = "vector_metadata.pkl",
                 min_similarity_threshold: float = 0.3,
                 max_context_messages: int = 5):
        """
        Initialize the vector service with FAISS index and sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model to use
            index_path: Path to save/load the FAISS index
            metadata_path: Path to save/load vector metadata
            min_similarity_threshold: Minimum similarity score for search results
            max_context_messages: Maximum number of context messages to return
        """
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.min_similarity_threshold = min_similarity_threshold
        self.max_context_messages = max_context_messages
        
        # Analytics tracking
        self._total_searches = 0
        self._successful_searches = 0
        self._total_results = 0
        
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
    
    def preprocess_query(self, query: str) -> str:
        """Clean and normalize query for better search"""
        # Remove extra whitespace and normalize
        query = " ".join(query.strip().lower().split())
        return query
    
    def expand_query(self, query: str) -> List[str]:
        """Generate alternative queries for better search coverage"""
        expanded = [query]
        
        # Add common variations
        if "?" in query:
            expanded.append(query.replace("?", ""))
        if "what" in query.lower():
            expanded.append(query.replace("what", "how"))
        if "how" in query.lower():
            expanded.append(query.replace("how", "what"))
        
        return expanded
    
    def validate_index(self) -> bool:
        """Validate FAISS index integrity"""
        try:
            if not hasattr(self, 'index') or not hasattr(self, 'metadata'):
                return False
            
            # Check if metadata and index are aligned
            if len(self.metadata) != self.index.ntotal:
                logger.warning(f"Index metadata mismatch: {len(self.metadata)} metadata vs {self.index.ntotal} vectors")
                return False
            
            # Check if index is not empty
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating index: {e}")
            return False
    
    def recover_index(self) -> bool:
        """Recover corrupted index by rebuilding"""
        try:
            logger.info("Attempting to recover corrupted index...")
            
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
            
            # Save clean index
            self._save_index()
            
            logger.info("Index recovery completed")
            return True
        except Exception as e:
            logger.error(f"Error recovering index: {e}")
            return False
    
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
    
    def search_similar_messages(self, query: str, conversation_id: Optional[str] = None, k: int = 5, min_score: float = None) -> List[Dict]:
        """
        Search for similar messages in the vector database with enhanced filtering
        
        Args:
            query: Search query text
            conversation_id: Optional conversation ID to filter results
            k: Number of results to return
            min_score: Minimum similarity score threshold (overrides default)
        
        Returns:
            List of dictionaries with similar messages and their metadata
        """
        try:
            # Update analytics
            self._total_searches += 1
            
            # Use provided min_score or default threshold
            threshold = min_score if min_score is not None else self.min_similarity_threshold
            
            # Preprocess query
            processed_query = self.preprocess_query(query)
            
            # Generate query embedding
            query_embedding = self.model.encode([processed_query], convert_to_tensor=False)
            
            # Search in FAISS index with more candidates for better filtering
            search_k = min(k * 3, self.index.ntotal)
            scores, indices = self.index.search(query_embedding.astype('float32'), search_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or score < threshold:  # Filter by similarity threshold
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
            
            # Update analytics
            if results:
                self._successful_searches += 1
                self._total_results += len(results)
            
            logger.info(f"Found {len(results)} similar messages for query: {query[:50]}... (min_score: {threshold})")
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

    def get_search_analytics(self) -> Dict:
        """Get analytics about search performance"""
        avg_results = self._total_results / max(self._total_searches, 1)
        return {
            "total_searches": self._total_searches,
            "successful_searches": self._successful_searches,
            "success_rate": self._successful_searches / max(self._total_searches, 1),
            "average_results_per_search": avg_results,
            "index_size": self.index.ntotal if hasattr(self, 'index') else 0,
            "metadata_size": len(self.metadata) if hasattr(self, 'metadata') else 0,
            "min_similarity_threshold": self.min_similarity_threshold
        }
    
    def search_by_topics(self, topics: List[str], conversation_id: Optional[str] = None, k: int = 3) -> List[Dict]:
        """
        Search for messages related to specific topics
        
        Args:
            topics: List of topics to search for
            conversation_id: Optional conversation ID to filter by
            k: Number of results per topic
        
        Returns:
            List of relevant messages grouped by topic
        """
        try:
            all_results = []
            
            for topic in topics:
                # Search for each topic
                topic_results = self.search_similar_messages(
                    query=topic,
                    conversation_id=conversation_id,
                    k=k,
                    min_score=0.3
                )
                
                # Add topic information to results
                for result in topic_results:
                    result['topic'] = topic
                    result['topic_relevance'] = result['score']
                
                all_results.extend(topic_results)
            
            # Remove duplicates and sort by relevance
            unique_results = {}
            for result in all_results:
                key = f"{result['conversation_id']}_{result['message_id']}"
                if key not in unique_results or result['score'] > unique_results[key]['score']:
                    unique_results[key] = result
            
            # Sort by score and return top results
            sorted_results = sorted(unique_results.values(), key=lambda x: x['score'], reverse=True)
            return sorted_results[:k * len(topics)]
            
        except Exception as e:
            logger.error(f"Error in topic-based search: {e}")
            return []
    
    def get_conversation_summary(self, conversation_id: str, k: int = 5) -> Dict:
        """
        Get a summary of key messages from a conversation
        
        Args:
            conversation_id: ID of the conversation
            k: Number of key messages to return
        
        Returns:
            Dictionary with conversation summary
        """
        try:
            # Get all messages for this conversation
            conversation_messages = [
                metadata for metadata in self.metadata 
                if metadata['conversation_id'] == conversation_id
            ]
            
            if not conversation_messages:
                return {"error": "No messages found for conversation"}
            
            # Get user questions
            user_messages = [
                msg for msg in conversation_messages 
                if msg['role'] == 'user'
            ]
            
            # Get assistant responses
            assistant_messages = [
                msg for msg in conversation_messages 
                if msg['role'] == 'assistant'
            ]
            
            # Get recent messages
            recent_messages = sorted(conversation_messages, key=lambda x: x['timestamp'])[-k:]
            
            return {
                "total_messages": len(conversation_messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "recent_messages": recent_messages,
                "last_user_question": user_messages[-1]['content_preview'] if user_messages else None,
                "conversation_start": conversation_messages[0]['timestamp'] if conversation_messages else None
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {"error": str(e)}
