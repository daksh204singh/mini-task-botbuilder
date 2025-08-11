#!/usr/bin/env python3
"""
Test Advanced RAG Improvements
Tests the enhanced RAG system with token management, summarization, and dynamic context
"""

import logging
import os
from services.rag_service import RAGService
from services.vector_service import VectorService
from services.database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_advanced_rag_features():
    """Test all advanced RAG features"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    rag_service = RAGService()
    vector_service = VectorService()
    database_service = DatabaseService()
    
    # Get a test conversation
    conversations = database_service.get_all_conversations()
    if not conversations:
        logger.error("No conversations found!")
        return
    
    conversation_id = conversations[0]["id"]
    conversation_name = conversations[0]["bot_name"]
    
    logger.info(f"🧪 Testing Advanced RAG Features for: {conversation_name}")
    logger.info(f"📋 Conversation ID: {conversation_id}")
    
    # Test 1: Token Counting
    logger.info(f"\n🔍 Test 1: Token Counting")
    test_text = "This is a test message for token counting."
    token_count = rag_service.count_tokens(test_text)
    logger.info(f"Text: '{test_text}'")
    logger.info(f"Token count: {token_count}")
    
    # Test 2: Conversation Summarization
    logger.info(f"\n🔍 Test 2: Conversation Summarization")
    summary = rag_service.summarize_conversation(conversation_id)
    logger.info(f"Generated summary: {summary}")
    
    # Test 3: Dynamic Context Management
    logger.info(f"\n🔍 Test 3: Dynamic Context Management")
    
    test_queries = [
        "How do I create a function?",
        "What are variables?",
        "Explain Python basics"
    ]
    
    for query in test_queries:
        logger.info(f"\n📝 Testing query: '{query}'")
        
        # Get dynamic context
        context = rag_service.get_dynamic_context(query, conversation_id)
        token_count = rag_service.count_tokens(context + query)
        
        logger.info(f"Context length: {len(context)} chars")
        logger.info(f"Total tokens (context + query): {token_count}")
        
        # Show context structure
        if "**Recent Context:**" in context:
            logger.info("✅ Using recent context strategy")
        elif "**Relevant Context:**" in context:
            logger.info("✅ Using semantic search strategy")
        elif "**Conversation Summary:**" in context:
            logger.info("✅ Using summarization strategy")
        else:
            logger.info("⚠️ No specific context strategy detected")
    
    # Test 4: Context Length Management
    logger.info(f"\n🔍 Test 4: Context Length Management")
    
    # Create a long context to test management
    long_context = """
**Conversation Summary:**
• Total messages: 15
• User questions: 8
• Assistant responses: 7
• Last question: How do I create a function in Python?

**Relevant Context:**
• User: How do I create a function?
• Assistant: To create a function in Python, you use the 'def' keyword followed by the function name and parameters.
• User: What are the different types of parameters?
• Assistant: Python supports several types of parameters including positional, keyword, default, and variable-length parameters.

**Topics Discussed:**
• Python programming
• Functions
• Parameters
• Variables
• Control structures
"""
    
    test_query = "How do I create a function?"
    managed_context = rag_service.manage_context_length(long_context, test_query, max_tokens=500)
    
    original_tokens = rag_service.count_tokens(long_context + test_query)
    managed_tokens = rag_service.count_tokens(managed_context + test_query)
    
    logger.info(f"Original context tokens: {original_tokens}")
    logger.info(f"Managed context tokens: {managed_tokens}")
    logger.info(f"Token reduction: {original_tokens - managed_tokens} tokens")
    
    # Test 5: Context Relevance Validation
    logger.info(f"\n🔍 Test 5: Context Relevance Validation")
    
    # Test with relevant query
    relevant_query = "How do I create a function?"
    relevant_context = rag_service.generate_context(relevant_query, conversation_id)
    relevant_validation = rag_service.validate_context_relevance(relevant_query, relevant_context)
    
    # Test with irrelevant query
    irrelevant_query = "What is quantum physics?"
    irrelevant_context = rag_service.generate_context(irrelevant_query, conversation_id)
    irrelevant_validation = rag_service.validate_context_relevance(irrelevant_query, irrelevant_context)
    
    logger.info(f"Relevant query validation score: {relevant_validation.get('relevance_score', 0):.2f}")
    logger.info(f"Irrelevant query validation score: {irrelevant_validation.get('relevance_score', 0):.2f}")
    
    if relevant_validation.get('relevance_score', 0) > irrelevant_validation.get('relevance_score', 0):
        logger.info("✅ Relevance validation working correctly")
    else:
        logger.warning("⚠️ Relevance validation may need adjustment")
    
    # Test 6: Full RAG Pipeline
    logger.info(f"\n🔍 Test 6: Full RAG Pipeline")
    
    test_query = "How do I create a function?"
    
    # Generate context
    context = rag_service.generate_context(test_query, conversation_id)
    
    # Generate system prompt
    persona = {"bot_name": conversation_name, "persona": conversations[0]["persona"]}
    system_prompt = rag_service.generate_system_prompt(persona)
    
    # Build full prompt
    full_prompt = rag_service.build_prompt(system_prompt, context, test_query, persona)
    
    total_tokens = rag_service.count_tokens(full_prompt)
    
    logger.info(f"Generated context: {len(context)} chars")
    logger.info(f"System prompt: {len(system_prompt)} chars")
    logger.info(f"Full prompt: {len(full_prompt)} chars")
    logger.info(f"Total tokens: {total_tokens}")
    
    if total_tokens <= rag_service.token_limit:
        logger.info("✅ Prompt within token limits")
    else:
        logger.warning(f"⚠️ Prompt exceeds token limit ({total_tokens} > {rag_service.token_limit})")
    
    # Test 7: Performance Metrics
    logger.info(f"\n🔍 Test 7: Performance Metrics")
    
    # Get vector stats
    vector_stats = vector_service.get_vector_stats()
    logger.info(f"Vector database stats: {vector_stats}")
    
    # Get search analytics
    search_analytics = vector_service.get_search_analytics()
    logger.info(f"Search analytics: {search_analytics}")
    
    logger.info("\n🎉 Advanced RAG Testing Completed!")

if __name__ == "__main__":
    test_advanced_rag_features()
