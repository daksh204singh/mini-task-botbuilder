#!/usr/bin/env python3
"""
RAG Implementation Test Script
Tests the current RAG system with dummy data and various scenarios
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

# Import our services
from services.rag_service import RAGService
from services.vector_service import VectorService
from services.database_service import DatabaseService
from services.gemini_service import GeminiService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGTester:
    def __init__(self):
        """Initialize the RAG tester with all services"""
        self.rag_service = RAGService()
        self.vector_service = VectorService()
        self.database_service = DatabaseService()
        
        # Initialize Gemini service with API key from environment
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                self.gemini_service = GeminiService(api_key)
                logger.info("✅ Gemini service initialized successfully")
            else:
                logger.warning("⚠️ No GEMINI_API_KEY found, skipping Gemini service")
                self.gemini_service = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Gemini service: {e}")
            self.gemini_service = None
        
    def create_dummy_conversation(self, conversation_id: str, topic: str) -> List[Dict]:
        """Create dummy conversation data for testing"""
        
        # Different conversation scenarios
        conversations = {
            "python_basics": [
                {"role": "user", "content": "What is Python?", "timestamp": datetime.now() - timedelta(hours=2)},
                {"role": "assistant", "content": "Python is a high-level programming language known for its simplicity and readability. It's great for beginners and widely used in data science, web development, and automation.", "timestamp": datetime.now() - timedelta(hours=2, minutes=5)},
                {"role": "user", "content": "How do I install Python?", "timestamp": datetime.now() - timedelta(hours=1, minutes=30)},
                {"role": "assistant", "content": "You can download Python from python.org. For beginners, I recommend using Anaconda which includes Python and many useful packages for data science.", "timestamp": datetime.now() - timedelta(hours=1, minutes=25)},
                {"role": "user", "content": "What are variables in Python?", "timestamp": datetime.now() - timedelta(hours=1)},
                {"role": "assistant", "content": "Variables in Python are containers for storing data values. You can create them by simply assigning a value: x = 5, name = 'John', is_valid = True.", "timestamp": datetime.now() - timedelta(hours=1, minutes=5)},
                {"role": "user", "content": "How do I create a function?", "timestamp": datetime.now() - timedelta(minutes=30)},
                {"role": "assistant", "content": "You create functions using the 'def' keyword: def greet(name): return f'Hello {name}'. Functions can take parameters and return values.", "timestamp": datetime.now() - timedelta(minutes=25)},
                {"role": "user", "content": "What are lists and how do I use them?", "timestamp": datetime.now() - timedelta(minutes=10)},
                {"role": "assistant", "content": "Lists are ordered collections of items. You can create them with square brackets: my_list = [1, 2, 3]. They're mutable and support indexing, slicing, and various methods like append(), remove(), etc.", "timestamp": datetime.now() - timedelta(minutes=5)}
            ],
            "machine_learning": [
                {"role": "user", "content": "What is machine learning?", "timestamp": datetime.now() - timedelta(hours=3)},
                {"role": "assistant", "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task.", "timestamp": datetime.now() - timedelta(hours=3, minutes=5)},
                {"role": "user", "content": "What are the main types of ML?", "timestamp": datetime.now() - timedelta(hours=2, minutes=30)},
                {"role": "assistant", "content": "The main types are: 1) Supervised Learning (classification, regression), 2) Unsupervised Learning (clustering, dimensionality reduction), 3) Reinforcement Learning (learning through interaction).", "timestamp": datetime.now() - timedelta(hours=2, minutes=25)},
                {"role": "user", "content": "How do I start with scikit-learn?", "timestamp": datetime.now() - timedelta(hours=1, minutes=45)},
                {"role": "assistant", "content": "Start by installing scikit-learn: pip install scikit-learn. Then import it: from sklearn import datasets, model_selection. Try the iris dataset for classification or boston dataset for regression.", "timestamp": datetime.now() - timedelta(hours=1, minutes=40)},
                {"role": "user", "content": "What is overfitting?", "timestamp": datetime.now() - timedelta(hours=1, minutes=15)},
                {"role": "assistant", "content": "Overfitting occurs when a model learns the training data too well, including noise and irrelevant patterns. It performs well on training data but poorly on new, unseen data. Solutions include regularization, cross-validation, and more training data.", "timestamp": datetime.now() - timedelta(hours=1, minutes=10)},
                {"role": "user", "content": "How do I evaluate model performance?", "timestamp": datetime.now() - timedelta(minutes=45)},
                {"role": "assistant", "content": "Use metrics like accuracy, precision, recall, F1-score for classification. For regression, use MSE, MAE, R-squared. Always use cross-validation to get reliable performance estimates.", "timestamp": datetime.now() - timedelta(minutes=40)}
            ],
            "web_development": [
                {"role": "user", "content": "What is React?", "timestamp": datetime.now() - timedelta(hours=4)},
                {"role": "assistant", "content": "React is a JavaScript library for building user interfaces, particularly single-page applications. It's developed by Facebook and uses a component-based architecture.", "timestamp": datetime.now() - timedelta(hours=4, minutes=5)},
                {"role": "user", "content": "How do I create a React component?", "timestamp": datetime.now() - timedelta(hours=3, minutes=30)},
                {"role": "assistant", "content": "You can create components using function syntax: function MyComponent() { return <div>Hello World</div> } or class syntax. Modern React prefers functional components with hooks.", "timestamp": datetime.now() - timedelta(hours=3, minutes=25)},
                {"role": "user", "content": "What are hooks in React?", "timestamp": datetime.now() - timedelta(hours=2, minutes=45)},
                {"role": "assistant", "content": "Hooks are functions that let you use state and other React features in functional components. Common hooks include useState, useEffect, useContext, and useRef.", "timestamp": datetime.now() - timedelta(hours=2, minutes=40)},
                {"role": "user", "content": "How do I handle forms in React?", "timestamp": datetime.now() - timedelta(hours=2, minutes=15)},
                {"role": "assistant", "content": "Use controlled components with state: const [value, setValue] = useState(''). Then use onChange handlers to update state: <input value={value} onChange={(e) => setValue(e.target.value)} />", "timestamp": datetime.now() - timedelta(hours=2, minutes=10)},
                {"role": "user", "content": "What is the virtual DOM?", "timestamp": datetime.now() - timedelta(hours=1, minutes=30)},
                {"role": "assistant", "content": "The virtual DOM is a lightweight copy of the actual DOM. React uses it to optimize updates by comparing virtual DOM trees and only updating what changed in the real DOM, improving performance.", "timestamp": datetime.now() - timedelta(hours=1, minutes=25)}
            ]
        }
        
        return conversations.get(topic, conversations["python_basics"])
    
    def populate_test_data(self):
        """Populate the system with test data"""
        logger.info("🔄 Populating test data...")
        
        # Create test conversations
        test_conversations = [
            ("python_basics", "Python Programming Basics"),
            ("machine_learning", "Machine Learning Fundamentals"),
            ("web_development", "React Web Development")
        ]
        
        # Create a test session ID
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        for topic, title in test_conversations:
            conversation_id = f"test_{topic}_{uuid.uuid4().hex[:8]}"
            
            # Create conversation in database
            self.database_service.create_conversation(
                session_id=session_id,
                bot_name=f"{title} Tutor",
                persona=f"a {topic} expert",
                model="Gemini 2.0 Flash"
            )
            
            # Get the actual conversation ID from the database
            conversations = self.database_service.get_session_conversations(session_id)
            conversation_id = conversations[-1]["id"]  # Get the most recent one
            
            # Get dummy messages
            messages = self.create_dummy_conversation(conversation_id, topic)
            
            # Store messages in database
            for msg in messages:
                message_id = str(uuid.uuid4())
                self.database_service.add_message(
                    conversation_id=conversation_id,
                    role=msg["role"],
                    content=msg["content"]
                )
            
            # Add embeddings to vector service
            vector_messages = []
            for msg in messages:
                message_id = str(uuid.uuid4())
                vector_messages.append({
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "role": msg["role"],
                    "content": msg["content"],
                    "content_preview": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"],
                    "timestamp": msg["timestamp"]
                })
            
            self.vector_service.add_conversation_embeddings(conversation_id, vector_messages)
            logger.info(f"✅ Created test conversation: {title} ({conversation_id})")
        
        logger.info("✅ Test data population complete!")
    
    def test_vector_search(self):
        """Test vector search functionality"""
        logger.info("\n🔍 Testing Vector Search...")
        
        # Test queries
        test_queries = [
            "How do I create a function?",
            "What is overfitting in machine learning?",
            "How do I handle forms in React?",
            "What are variables?",
            "Explain the virtual DOM"
        ]
        
        for query in test_queries:
            logger.info(f"\n📝 Query: '{query}'")
            
            # Search across all conversations
            results = self.vector_service.search_similar_messages(query, k=3, min_score=0.3)
            
            if results:
                logger.info(f"✅ Found {len(results)} relevant results:")
                for i, result in enumerate(results[:2], 1):  # Show top 2
                    logger.info(f"  {i}. [{result['role']}] {result['content_preview'][:100]}... (score: {result['score']:.3f})")
            else:
                logger.warning(f"❌ No relevant results found for: {query}")
    
    def test_conversation_context(self):
        """Test conversation-specific context retrieval"""
        logger.info("\n🎯 Testing Conversation Context...")
        
        # Get a test conversation ID
        conversations = self.database_service.get_all_conversations()
        if not conversations:
            logger.error("❌ No test conversations found!")
            return
        
        conversation_id = conversations[0]["id"]
        logger.info(f"📋 Testing context for conversation: {conversation_id}")
        
        # Test queries specific to this conversation
        test_queries = [
            "What did we discuss about functions?",
            "Can you remind me about variables?",
            "How do I install Python again?"
        ]
        
        for query in test_queries:
            logger.info(f"\n📝 Query: '{query}'")
            
            # Get conversation-specific context
            context = self.rag_service.generate_context(query, conversation_id)
            
            if context:
                logger.info(f"✅ Generated context ({len(context)} chars):")
                # Show first 200 chars of context
                preview = context[:200] + "..." if len(context) > 200 else context
                logger.info(f"  {preview}")
            else:
                logger.warning(f"❌ No context generated for: {query}")
    
    def test_topic_extraction(self):
        """Test topic extraction from conversations"""
        logger.info("\n🏷️ Testing Topic Extraction...")
        
        conversations = self.database_service.get_all_conversations()
        if not conversations:
            logger.error("❌ No test conversations found!")
            return
        
        for conv in conversations[:2]:  # Test first 2 conversations
            conversation_id = conv["id"]
            logger.info(f"\n📋 Extracting topics for: {conv['bot_name']}")
            
            topics = self.rag_service.extract_topics_from_conversation(conversation_id)
            
            if topics:
                logger.info(f"✅ Extracted topics: {', '.join(topics)}")
            else:
                logger.warning(f"❌ No topics extracted")
    
    def test_conversation_summary(self):
        """Test conversation summary generation"""
        logger.info("\n📊 Testing Conversation Summary...")
        
        conversations = self.database_service.get_all_conversations()
        if not conversations:
            logger.error("❌ No test conversations found!")
            return
        
        for conv in conversations:
            conversation_id = conv["id"]
            logger.info(f"\n📋 Summary for: {conv['bot_name']}")
            
            summary = self.rag_service.get_conversation_summary(conversation_id)
            
            if summary:
                logger.info(f"✅ Summary: {summary['total_messages']} messages, "
                          f"{summary['user_messages']} user, "
                          f"{summary['assistant_messages']} assistant")
                if summary.get('last_user_question'):
                    logger.info(f"   Last question: {summary['last_user_question'][:100]}...")
            else:
                logger.warning(f"❌ No summary generated")
    
    def test_full_rag_pipeline(self):
        """Test the complete RAG pipeline"""
        logger.info("\n🚀 Testing Full RAG Pipeline...")
        
        conversations = self.database_service.get_all_conversations()
        if not conversations:
            logger.error("❌ No test conversations found!")
            return
        
        conversation_id = conversations[0]["id"]
        conv = conversations[0]
        
        # Test query
        test_query = "How do I create a function in Python?"
        logger.info(f"\n📝 Test Query: '{test_query}'")
        logger.info(f"📋 Conversation: {conv['bot_name']}")
        
        # Generate context
        context = self.rag_service.generate_context(test_query, conversation_id)
        logger.info(f"✅ Context generated: {len(context)} characters")
        
        # Generate system prompt
        persona = {"bot_name": conv["bot_name"], "persona": conv["persona"]}
        system_prompt = self.rag_service.generate_system_prompt(persona)
        logger.info(f"✅ System prompt: {len(system_prompt)} characters")
        
        # Build complete prompt
        full_prompt = self.rag_service.build_prompt(system_prompt, context, test_query, persona)
        logger.info(f"✅ Full prompt: {len(full_prompt)} characters")
        
        # Show prompt preview
        preview = full_prompt[:300] + "..." if len(full_prompt) > 300 else full_prompt
        logger.info(f"📄 Prompt preview:\n{preview}")
    
    def test_analytics(self):
        """Test analytics and statistics"""
        logger.info("\n📈 Testing Analytics...")
        
        # Vector stats
        vector_stats = self.rag_service.get_vector_stats()
        logger.info(f"✅ Vector Stats: {vector_stats}")
        
        # Search analytics
        search_analytics = self.rag_service.get_search_analytics()
        logger.info(f"✅ Search Analytics: {search_analytics}")
    
    def run_all_tests(self):
        """Run all RAG tests"""
        logger.info("🧪 Starting RAG Implementation Tests...")
        
        try:
            # Populate test data
            self.populate_test_data()
            
            # Run individual tests
            self.test_vector_search()
            self.test_conversation_context()
            self.test_topic_extraction()
            self.test_conversation_summary()
            self.test_full_rag_pipeline()
            self.test_analytics()
            
            logger.info("\n🎉 All RAG tests completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main test runner"""
    tester = RAGTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
