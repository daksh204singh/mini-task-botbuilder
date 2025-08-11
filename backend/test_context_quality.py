#!/usr/bin/env python3
"""
Test Context Quality Improvements
Tests the enhanced RAG system for better context relevance and LLM responses
"""

import logging
from services.rag_service import RAGService
from services.vector_service import VectorService
from services.database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_context_quality():
    """Test the improved context quality and relevance"""
    
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
    
    logger.info(f"🧪 Testing Context Quality for: {conversation_name}")
    logger.info(f"📋 Conversation ID: {conversation_id}")
    
    # Test 1: Test different query types
    test_queries = [
        "How do I create a function?",
        "What are variables?",
        "Explain Python basics",
        "How do I install packages?",
        "What is machine learning?"
    ]
    
    for query in test_queries:
        logger.info(f"\n🔍 Testing Query: '{query}'")
        
        # Get context
        context = rag_service.generate_context(query, conversation_id)
        
        if context:
            logger.info(f"✅ Context generated ({len(context)} chars)")
            
            # Show context structure
            if "**Relevant Context:**" in context:
                relevant_section = context.split("**Relevant Context:**")[1].split("**")[0]
                logger.info(f"📄 Relevant Context:\n{relevant_section.strip()}")
            
            if "**Topics Discussed:**" in context:
                topics_section = context.split("**Topics Discussed:**")[1].split("**")[0]
                logger.info(f"🏷️ Topics:\n{topics_section.strip()}")
        else:
            logger.warning("❌ No context generated")
    
    # Test 2: Test vector search quality
    logger.info(f"\n🔍 Test 2: Vector Search Quality")
    
    test_query = "How do I create a function?"
    results = vector_service.search_similar_messages(test_query, conversation_id, k=3, min_score=0.25)
    
    logger.info(f"Found {len(results)} results with threshold 0.25")
    for i, result in enumerate(results, 1):
        logger.info(f"  {i}. Score: {result['score']:.3f} | {result['role']}: {result['content_preview'][:80]}...")
    
    # Test 3: Test prompt building
    logger.info(f"\n🔍 Test 3: Prompt Quality")
    
    context = rag_service.generate_context("How do I create a function?", conversation_id)
    persona = {"bot_name": conversation_name, "persona": conversations[0]["persona"]}
    system_prompt = rag_service.generate_system_prompt(persona)
    full_prompt = rag_service.build_prompt(system_prompt, context, "How do I create a function?", persona)
    
    logger.info(f"✅ Full prompt length: {len(full_prompt)} chars")
    
    # Show prompt structure
    if "**Instructions:**" in full_prompt:
        instructions_section = full_prompt.split("**Instructions:**")[1].split("Assistant:")[0]
        logger.info(f"📄 Instructions:\n{instructions_section.strip()}")
    
    # Test 4: Test context relevance scoring
    logger.info(f"\n🔍 Test 4: Context Relevance")
    
    # Test with a query that should have high relevance
    high_relevance_query = "How do I create a function?"
    high_context = rag_service.generate_context(high_relevance_query, conversation_id)
    
    # Test with a query that should have low relevance
    low_relevance_query = "What is quantum physics?"
    low_context = rag_service.generate_context(low_relevance_query, conversation_id)
    
    logger.info(f"High relevance query context length: {len(high_context)} chars")
    logger.info(f"Low relevance query context length: {len(low_context)} chars")
    
    if len(high_context) > len(low_context):
        logger.info("✅ Context length correctly reflects relevance")
    else:
        logger.warning("⚠️ Context length doesn't reflect relevance")
    
    logger.info("\n🎉 Context Quality Test Completed!")

if __name__ == "__main__":
    test_context_quality()
