import logging
from typing import List, Dict, Optional, Tuple
from .vector_service import VectorService
from .database_service import DatabaseService
import re
import tiktoken  # For token counting

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Initialize RAG service with vector and database services"""
        try:
            self.vector_service = VectorService()
            self.database_service = DatabaseService()
            self.token_limit = 4000  # Conservative token limit
            self.summary_length = 200  # Target summary length
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            self.vector_service = None
            self.database_service = None
    
    def count_tokens(self, text: str, model_name: str = "gpt-3.5-turbo") -> int:
        """
        Count tokens in text using tiktoken
        
        Args:
            text: Text to count tokens for
            model_name: Model name for encoding
        
        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(model_name)
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Could not count tokens: {e}")
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def summarize_conversation(self, conversation_id: str) -> str:
        """
        Generate a summary of the conversation using the LLM
        
        Args:
            conversation_id: ID of the conversation to summarize
        
        Returns:
            Summary string
        """
        try:
            conversation_messages = self.vector_service.get_conversation_messages(conversation_id)
            if not conversation_messages or len(conversation_messages) < 3:
                return ""
            
            # Get recent messages for summarization
            recent_messages = conversation_messages[-10:]  # Last 10 messages
            
            # Format messages for summarization
            formatted_messages = []
            for msg in recent_messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content_preview'][:200]  # Limit content length
                formatted_messages.append(f"{role}: {content}")
            
            conversation_text = "\n".join(formatted_messages)
            
            # Create summarization prompt
            summary_prompt = f"""
Summarize the following conversation in 2-3 sentences, focusing on:
1. The main topics discussed
2. Key questions asked
3. Important concepts covered

Conversation:
{conversation_text}

Summary:"""
            
            # For now, return a simple summary based on topics
            # In production, you'd call the LLM here
            topics = self.extract_topics_from_conversation(conversation_id, max_messages=5)
            if topics:
                return f"Discussed: {', '.join(topics[:3])}. Total messages: {len(conversation_messages)}"
            else:
                return f"Conversation with {len(conversation_messages)} messages"
                
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return ""
    
    def manage_context_length(self, context: str, query: str, max_tokens: int = None) -> str:
        """
        Manage context length to stay within token limits
        
        Args:
            context: Generated context
            query: User query
            max_tokens: Maximum tokens allowed
        
        Returns:
            Managed context string
        """
        if max_tokens is None:
            max_tokens = self.token_limit
        
        try:
            # Count tokens in context + query
            total_tokens = self.count_tokens(context + query)
            
            if total_tokens <= max_tokens:
                return context
            
            logger.info(f"Context too long ({total_tokens} tokens), reducing...")
            
            # Strategy 1: Remove less important sections
            if "**Topics Discussed:**" in context:
                context = context.split("**Topics Discussed:**")[0].strip()
            
            if "**Conversation Summary:**" in context:
                # Keep only essential summary info
                summary_section = context.split("**Conversation Summary:**")[1].split("**")[0]
                essential_summary = f"**Conversation Summary:**\n• Total messages: {summary_section.split('Total messages:')[1].split('•')[0].strip()}\n\n"
                context = context.replace(context.split("**Conversation Summary:**")[1].split("**")[0], essential_summary)
            
            # Strategy 2: Truncate relevant context
            if "**Relevant Context:**" in context:
                relevant_section = context.split("**Relevant Context:**")[1].split("**")[0]
                lines = relevant_section.strip().split('\n')
                if len(lines) > 4:  # Keep only first 2 relevant items
                    truncated_relevant = '\n'.join(lines[:4]) + '\n'
                    context = context.replace(relevant_section, truncated_relevant)
            
            # Check if still too long
            if self.count_tokens(context + query) > max_tokens:
                # Strategy 3: Keep only the most essential parts
                if "**Relevant Context:**" in context:
                    relevant_section = context.split("**Relevant Context:**")[1].split("**")[0]
                    lines = relevant_section.strip().split('\n')
                    if len(lines) > 2:  # Keep only first relevant item
                        minimal_relevant = '\n'.join(lines[:2]) + '\n'
                        context = f"**Relevant Context:**\n{minimal_relevant}\n"
                else:
                    # Fallback: very minimal context
                    context = ""
            
            logger.info(f"Reduced context to {self.count_tokens(context + query)} tokens")
            return context
            
        except Exception as e:
            logger.error(f"Error managing context length: {e}")
            return context
    
    def get_dynamic_context(self, query: str, conversation_id: str) -> str:
        """
        Get dynamic context based on query relevance and conversation state
        
        Args:
            query: Current user query
            conversation_id: Conversation ID
        
        Returns:
            Dynamic context string
        """
        try:
            # Get conversation info
            conversation_messages = self.vector_service.get_conversation_messages(conversation_id)
            if not conversation_messages:
                return ""
            
            # Determine context strategy based on conversation length
            if len(conversation_messages) <= 3:
                # Short conversation: use recent context
                return self._get_recent_context(conversation_messages)
            elif len(conversation_messages) <= 10:
                # Medium conversation: use semantic search + recent
                return self._get_medium_context(query, conversation_id, conversation_messages)
            else:
                # Long conversation: use summarization + semantic search
                return self._get_long_context(query, conversation_id, conversation_messages)
                
        except Exception as e:
            logger.error(f"Error getting dynamic context: {e}")
            return ""
    
    def _get_recent_context(self, messages: List[Dict]) -> str:
        """Get context for short conversations"""
        recent_messages = messages[-4:]  # Last 4 messages
        context_parts = []
        
        for msg in recent_messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg['content_preview'][:150] + "..." if len(msg['content_preview']) > 150 else msg['content_preview']
            context_parts.append(f"• {role}: {content}")
        
        return "**Recent Context:**\n" + "\n".join(context_parts) + "\n\n"
    
    def _get_medium_context(self, query: str, conversation_id: str, messages: List[Dict]) -> str:
        """Get context for medium conversations"""
        context_parts = []
        
        # Get semantic search results with lower threshold
        relevant_messages = self.vector_service.search_similar_messages(query, conversation_id, k=2, min_score=0.15)
        if relevant_messages:
            context_parts.append("**Relevant Context:**")
            for msg in relevant_messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content_preview'][:150] + "..." if len(msg['content_preview']) > 150 else msg['content_preview']
                context_parts.append(f"• {role}: {content}")
            context_parts.append("")
        
        # Add recent questions as fallback
        if not relevant_messages:
            user_messages = [msg for msg in messages if msg['role'] == 'user']
            if user_messages:
                recent_questions = user_messages[-2:]
                context_parts.append("**Recent Questions:**")
                for i, msg in enumerate(recent_questions, 1):
                    question = msg['content_preview'][:100] + "..." if len(msg['content_preview']) > 100 else msg['content_preview']
                    context_parts.append(f"{i}. {question}")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _get_long_context(self, query: str, conversation_id: str, messages: List[Dict]) -> str:
        """Get context for long conversations using summarization"""
        context_parts = []
        
        # Get conversation summary
        summary = self.summarize_conversation(conversation_id)
        if summary:
            context_parts.append("**Conversation Summary:**")
            context_parts.append(f"• {summary}")
            context_parts.append("")
        
        # Get semantic search results with lower threshold
        relevant_messages = self.vector_service.search_similar_messages(query, conversation_id, k=2, min_score=0.15)
        if relevant_messages:
            context_parts.append("**Relevant Context:**")
            for msg in relevant_messages:
                role = "User" if msg['role'] == 'user' else "Assistant"
                content = msg['content_preview'][:150] + "..." if len(msg['content_preview']) > 150 else msg['content_preview']
                context_parts.append(f"• {role}: {content}")
            context_parts.append("")
        
        # Add topics if we have relevant context
        if relevant_messages:
            topics = self.extract_topics_from_conversation(conversation_id, max_messages=5)
            if topics:
                context_parts.append("**Topics Discussed:**")
                for topic in topics[:3]:
                    context_parts.append(f"• {topic}")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def generate_context(self, query: str, conversation_id: str, messages: List[Dict] = None) -> str:
        """
        Generate focused and relevant context for a query using advanced techniques
        
        Args:
            query: Current user query
            conversation_id: ID of the conversation
            messages: Optional list of recent messages for additional context
        
        Returns:
            Formatted context string
        """
        if not self.vector_service:
            return ""
        
        try:
            # Use dynamic context management
            context = self.get_dynamic_context(query, conversation_id)
            
            # Manage context length to stay within token limits
            managed_context = self.manage_context_length(context, query)
            
            # Validate context relevance
            validation = self.validate_context_relevance(query, managed_context)
            
            if validation.get("relevance_score", 0) < 0.3:
                logger.warning(f"Low context relevance ({validation['relevance_score']:.2f}) for query: {query}")
                if validation.get("issues"):
                    logger.warning(f"Context issues: {validation['issues']}")
            
            logger.info(f"Generated managed context: {len(managed_context)} chars, {self.count_tokens(managed_context + query)} tokens")
            
            return managed_context
            
        except Exception as e:
            logger.error(f"Error generating context: {e}")
            return ""
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a summary of key messages from a conversation
        
        Args:
            conversation_id: ID of the conversation
        
        Returns:
            Dictionary with conversation summary
        """
        try:
            conversation_messages = self.vector_service.get_conversation_messages(conversation_id)
            
            if not conversation_messages:
                return None
            
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
            
            return {
                "total_messages": len(conversation_messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "last_user_question": user_messages[-1]['content_preview'] if user_messages else None,
                "conversation_start": conversation_messages[0]['timestamp'] if conversation_messages else None
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return None
    
    def extract_topics_from_conversation(self, conversation_id: str, max_messages: int = 10) -> List[str]:
        """
        Extract key topics from a conversation using LLM-based semantic analysis
        
        Args:
            conversation_id: ID of the conversation
            max_messages: Maximum number of recent messages to analyze
        
        Returns:
            List of extracted topics
        """
        try:
            # Get recent messages for this conversation
            conversation_messages = self.vector_service.get_conversation_messages(conversation_id)
            
            if not conversation_messages:
                return []
            
            # Use LLM-based topic extraction
            topics = self.extract_topics_with_llm(conversation_messages, max_messages)
            
            logger.info(f"Extracted topics for conversation {conversation_id}: {topics}")
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics from conversation: {e}")
            return []
    
    def extract_topics_with_llm(self, conversation_messages: List[Dict], max_messages: int = 10) -> List[str]:
        """
        Extract topics using semantic analysis with vector search
        
        Args:
            conversation_messages: List of conversation messages
            max_messages: Maximum number of recent messages to analyze
        
        Returns:
            List of extracted topics
        """
        try:
            if not conversation_messages:
                return []
            
            # Get recent messages
            recent_messages = conversation_messages[-max_messages:]
            
            # Combine content for analysis
            combined_content = " ".join([msg['content_preview'] for msg in recent_messages])
            
            # Use semantic topic extraction
            topics = self._extract_topics_semantic(combined_content, recent_messages)
            
            logger.info(f"Semantic topic extraction found: {topics}")
            return topics
            
        except Exception as e:
            logger.error(f"Error in semantic topic extraction: {e}")
            return self._extract_topics_fallback(combined_content)
    
    def _extract_topics_semantic(self, content: str, messages: List[Dict]) -> List[str]:
        """
        Extract topics using semantic analysis and vector search
        
        Args:
            content: Combined conversation content
            messages: Recent conversation messages
        
        Returns:
            List of extracted topics
        """
        try:
            # Define topic categories with their related terms
            topic_categories = {
                "programming": ["python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust", "swift", "kotlin"],
                "web development": ["html", "css", "react", "vue", "angular", "node.js", "express", "django", "flask", "spring"],
                "data science": ["machine learning", "artificial intelligence", "deep learning", "neural networks", "data science"],
                "databases": ["database", "sql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch"],
                "mathematics": ["mathematics", "algebra", "geometry", "calculus", "statistics", "probability"],
                "computer science": ["algorithms", "data structures", "software engineering", "system design"],
                "devops": ["docker", "kubernetes", "git", "github", "ci/cd", "deployment"],
                "frameworks": ["scikit-learn", "tensorflow", "pytorch", "pandas", "numpy", "matplotlib"]
            }
            
            found_topics = []
            content_lower = content.lower()
            
            # First pass: Direct keyword matching
            for category, terms in topic_categories.items():
                for term in terms:
                    if term in content_lower:
                        found_topics.append(category)
                        break  # Only add category once
            
            # Second pass: Semantic search for related concepts
            if self.vector_service and found_topics:
                for category in found_topics[:3]:  # Limit to top 3 categories
                    try:
                        # Search for semantically similar content
                        similar_messages = self.vector_service.search_similar_messages(
                            category, k=3, min_score=0.2
                        )
                        
                        for msg in similar_messages:
                            msg_content = msg['content_preview'].lower()
                            
                            # Check for additional topics in similar messages
                            for cat, terms in topic_categories.items():
                                if cat not in found_topics:
                                    for term in terms:
                                        if term in msg_content:
                                            found_topics.append(cat)
                                            break
                    except Exception as e:
                        logger.warning(f"Error in semantic topic search: {e}")
            
            # Third pass: Extract specific concepts from recent messages
            specific_concepts = []
            for msg in messages:
                msg_content = msg['content_preview'].lower()
                
                # Look for specific programming concepts
                programming_concepts = [
                    "variables", "functions", "classes", "objects", "methods", "inheritance", 
                    "polymorphism", "encapsulation", "abstraction", "interfaces", "modules", 
                    "packages", "libraries", "frameworks", "debugging", "testing", "deployment"
                ]
                
                for concept in programming_concepts:
                    if concept in msg_content and concept not in specific_concepts:
                        specific_concepts.append(concept)
            
            # Combine category topics with specific concepts
            all_topics = found_topics + specific_concepts[:3]  # Limit specific concepts
            
            # Remove duplicates and limit to 5 topics
            unique_topics = list(dict.fromkeys(all_topics))[:5]
            
            return unique_topics
            
        except Exception as e:
            logger.error(f"Error in semantic topic extraction: {e}")
            return []
    
    def _extract_topics_fallback(self, content: str) -> List[str]:
        """
        Fallback topic extraction using enhanced keyword matching
        This is used when LLM is not available or as a backup
        """
        try:
            # Enhanced educational topics with better coverage
            educational_topics = [
                # Programming & Development
                "programming", "python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust", "swift", "kotlin",
                "data structures", "algorithms", "object-oriented programming", "functional programming", "web development",
                "frontend", "backend", "full-stack", "api", "rest", "graphql", "microservices", "docker", "kubernetes",
                "software engineering", "system design", "database design", "testing", "debugging", "version control",
                
                # Data Science & ML
                "machine learning", "artificial intelligence", "deep learning", "neural networks", "data science",
                "statistics", "probability", "linear algebra", "calculus", "optimization", "scikit-learn", "tensorflow",
                "pytorch", "pandas", "numpy", "matplotlib", "seaborn", "jupyter", "data visualization", "big data",
                
                # Web Technologies
                "html", "css", "react", "vue", "angular", "node.js", "express", "django", "flask", "spring", "laravel",
                "database", "sql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "git", "github",
                "responsive design", "user experience", "accessibility", "performance optimization",
                
                # Computer Science
                "computer science", "distributed systems", "networking", "operating systems", "computer architecture",
                "compilers", "automata theory", "complexity theory", "cryptography", "security", "cybersecurity",
                
                # Mathematics
                "mathematics", "algebra", "geometry", "trigonometry", "calculus", "differential equations",
                "number theory", "combinatorics", "graph theory", "topology", "analysis", "abstract algebra",
                "discrete mathematics", "linear algebra", "probability theory", "statistical analysis",
                
                # Sciences
                "physics", "chemistry", "biology", "genetics", "evolution", "ecology", "astronomy", "geology",
                "psychology", "neuroscience", "cognitive science", "anthropology", "sociology", "environmental science",
                
                # Humanities
                "history", "literature", "philosophy", "ethics", "logic", "rhetoric", "linguistics", "art",
                "music", "economics", "political science", "geography", "archaeology", "cultural studies"
            ]
            
            # Programming concepts and patterns
            programming_concepts = [
                "variables", "functions", "classes", "objects", "methods", "inheritance", "polymorphism",
                "encapsulation", "abstraction", "interfaces", "modules", "packages", "libraries", "frameworks",
                "debugging", "testing", "unit tests", "integration tests", "deployment", "version control",
                "code review", "refactoring", "design patterns", "clean code", "agile", "scrum", "kanban",
                "continuous integration", "continuous deployment", "devops", "cloud computing", "serverless"
            ]
            
            content_lower = content.lower()
            found_topics = []
            
            # Check for educational topics
            for topic in educational_topics:
                if topic.lower() in content_lower:
                    found_topics.append(topic)
            
            # Check for programming concepts
            for concept in programming_concepts:
                if concept.lower() in content_lower and concept not in found_topics:
                    found_topics.append(concept)
            
            # Use semantic search to find related concepts
            if found_topics:
                for topic in found_topics[:3]:
                    try:
                        similar_messages = self.vector_service.search_similar_messages(
                            topic, k=2, min_score=0.2
                        )
                        for msg in similar_messages:
                            msg_content = msg['content_preview'].lower()
                            for potential_topic in educational_topics + programming_concepts:
                                if (potential_topic.lower() in msg_content and 
                                    potential_topic not in found_topics and 
                                    len(potential_topic) > 2):
                                    found_topics.append(potential_topic)
                    except Exception as e:
                        logger.warning(f"Error in semantic topic search: {e}")
            
            # Remove duplicates and limit to 5 topics
            unique_topics = list(dict.fromkeys(found_topics))[:5]
            return unique_topics
            
        except Exception as e:
            logger.error(f"Error in fallback topic extraction: {e}")
            return []
    
    def build_prompt(self, system_prompt: str, context: str, user_query: str, persona: Dict = None) -> str:
        """
        Build a focused prompt with clear instructions for contextual responses
        
        Args:
            system_prompt: Base system prompt
            context: Generated RAG context
            user_query: Current user query
            persona: Optional persona information
        
        Returns:
            Complete formatted prompt
        """
        try:
            if context:
                # Build focused prompt with clear instructions
                context_prompt = f"""
{context}

**Current Question:** {user_query}

**Instructions:**
1. Use ONLY the relevant context above to answer the current question
2. If the context contains information that directly answers the question, reference it specifically
3. If the context is not relevant to the current question, ignore it and provide a general answer
4. Do not make up information that's not in the context
5. If the context shows previous explanations, build upon them but don't repeat unnecessarily
6. Keep your response focused and relevant to the current question
7. Use markdown formatting for better readability

Please provide a helpful response based on the context:"""
                full_prompt = f"{system_prompt}\n\n{context_prompt}\n\nAssistant:"
            else:
                # No context found, use direct approach
                full_prompt = f"{system_prompt}\n\nUser: {user_query}\n\nAssistant:"
            
            logger.info(f"Built focused prompt with context: {bool(context)}, length: {len(full_prompt)} chars")
            return full_prompt
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            # Fallback to simple prompt
            return f"{system_prompt}\n\nUser: {user_query}\n\nAssistant:"
    
    def generate_system_prompt(self, persona: Dict = None) -> str:
        """
        Generate system prompt based on persona
        
        Args:
            persona: Persona information with bot_name and persona description
        
        Returns:
            System prompt string
        """
        if persona:
            bot_name = persona.get('bot_name', 'Assistant')
            persona_desc = persona.get('persona', 'a helpful assistant')
            return f"You are a tutor named {bot_name}, acting as {persona_desc}. Help the user with their questions. Use markdown formatting for your output."
        return "You are a helpful AI assistant. Use markdown formatting for your output."
    
    def get_conversation_insights(self, conversation_id: str) -> Dict:
        """
        Get comprehensive insights about a conversation
        
        Args:
            conversation_id: ID of the conversation
        
        Returns:
            Dictionary with conversation insights
        """
        if not self.database_service:
            return {"error": "Database service not available"}
        
        return self.database_service.get_conversation_insights(conversation_id)
    
    def update_conversation_summary(self, conversation_id: str, topics: List[str], key_questions: List[str], learning_progress: str) -> bool:
        """
        Update conversation summary in database
        
        Args:
            conversation_id: ID of the conversation
            topics: List of topics discussed
            key_questions: List of key questions asked
            learning_progress: Learning progress summary
        
        Returns:
            Success status
        """
        if not self.database_service:
            return False
        
        return self.database_service.update_conversation_summary(conversation_id, topics, key_questions, learning_progress)
    
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

    def validate_context_relevance(self, query: str, context: str) -> Dict:
        """
        Validate the relevance of generated context to the query
        
        Args:
            query: The user query
            context: Generated context
        
        Returns:
            Dictionary with relevance analysis
        """
        try:
            analysis = {
                "query": query,
                "context_length": len(context),
                "has_relevant_context": False,
                "context_sections": {},
                "relevance_score": 0.0,
                "issues": []
            }
            
            if not context:
                analysis["issues"].append("No context generated")
                return analysis
            
            # Analyze context sections
            sections = {
                "conversation_summary": "**Conversation Summary:**" in context,
                "relevant_context": "**Relevant Context:**" in context,
                "recent_questions": "**Recent Questions:**" in context,
                "topics": "**Topics Discussed:**" in context,
                "recent_context": "**Recent Context:**" in context
            }
            
            analysis["context_sections"] = sections
            
            # Check if we have relevant context
            if sections["relevant_context"]:
                relevant_section = context.split("**Relevant Context:**")[1].split("**")[0]
                if relevant_section.strip():
                    analysis["has_relevant_context"] = True
                    analysis["relevance_score"] += 0.7
                else:
                    analysis["issues"].append("Relevant context section is empty")
            elif sections["recent_context"]:
                # Recent context is also relevant
                analysis["has_relevant_context"] = True
                analysis["relevance_score"] += 0.5
            elif sections["recent_questions"]:
                # Recent questions provide some context
                analysis["relevance_score"] += 0.3
            else:
                analysis["issues"].append("No relevant context section found")
            
            # Check if context is too long (might overwhelm the LLM)
            if len(context) > 1000:
                analysis["issues"].append("Context is too long (may overwhelm LLM)")
                analysis["relevance_score"] -= 0.1
            
            # Check if context is too short (might not be helpful)
            if len(context) < 50:
                analysis["issues"].append("Context is too short (may not be helpful)")
                analysis["relevance_score"] -= 0.2
            
            # Check for query-context overlap (improved)
            query_words = set(query.lower().split())
            context_words = set(context.lower().split())
            overlap = len(query_words.intersection(context_words))
            
            if overlap > 0:
                analysis["relevance_score"] += min(0.3, overlap * 0.1)  # Cap at 0.3
            else:
                # Check for semantic similarity in topics
                if sections["topics"]:
                    topics_section = context.split("**Topics Discussed:**")[1].split("**")[0]
                    if any(word in topics_section.lower() for word in query_words):
                        analysis["relevance_score"] += 0.2
                else:
                    analysis["issues"].append("No word overlap between query and context")
            
            # Bonus for having multiple context types
            context_types = sum(sections.values())
            if context_types >= 2:
                analysis["relevance_score"] += 0.1
            
            # Normalize relevance score
            analysis["relevance_score"] = max(0.0, min(1.0, analysis["relevance_score"]))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error validating context relevance: {e}")
            return {
                "query": query,
                "error": str(e),
                "relevance_score": 0.0
            }
