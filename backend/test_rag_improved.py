#!/usr/bin/env python3
"""
Improved RAG Implementation Test
Tests the enhanced RAG system with all fixes applied
"""

import logging
from services.rag_service import RAGService
from services.vector_service import VectorService
from services.database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_improved_rag():
    """Test the improved RAG implementation"""
    
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
    
    logger.info(f"🧪 Testing Improved RAG for: {conversation_name}")
    logger.info(f"📋 Conversation ID: {conversation_id}")
    
    # Test 1: Context Generation with Lower Threshold
    logger.info("\n🔍 Test 1: Context Generation")
    test_query = "How do I create a function?"
    context = rag_service.generate_context(test_query, conversation_id)
    
    if context:
        logger.info(f"✅ Context generated successfully ({len(context)} chars)")
        # Show first 300 chars
        preview = context[:300] + "..." if len(context) > 300 else context
        logger.info(f"📄 Context preview:\n{preview}")
    else:
        logger.warning("❌ No context generated")
    
    # Test 2: Topic Extraction
    logger.info("\n🏷️ Test 2: Topic Extraction")
    topics = rag_service.extract_topics_from_conversation(conversation_id)
    
    if topics:
        logger.info(f"✅ Topics extracted: {', '.join(topics)}")
    else:
        logger.warning("❌ No topics extracted")
    
    # Test 3: Conversation Summary
    logger.info("\n📊 Test 3: Conversation Summary")
    summary = rag_service.get_conversation_summary(conversation_id)
    
    if summary:
        logger.info(f"✅ Summary: {summary['total_messages']} messages, "
                   f"{summary['user_messages']} user, "
                   f"{summary['assistant_messages']} assistant")
        if summary.get('last_user_question'):
            logger.info(f"   Last question: {summary['last_user_question'][:100]}...")
    else:
        logger.warning("❌ No summary generated")
    
    # Test 4: Full RAG Pipeline
    logger.info("\n🚀 Test 4: Full RAG Pipeline")
    
    # Generate system prompt
    persona = {"bot_name": conversation_name, "persona": conversations[0]["persona"]}
    system_prompt = rag_service.generate_system_prompt(persona)
    logger.info(f"✅ System prompt: {len(system_prompt)} chars")
    
    # Build complete prompt
    full_prompt = rag_service.build_prompt(system_prompt, context, test_query, persona)
    logger.info(f"✅ Full prompt: {len(full_prompt)} chars")
    
    # Show prompt preview
    preview = full_prompt[:400] + "..." if len(full_prompt) > 400 else full_prompt
    logger.info(f"📄 Prompt preview:\n{preview}")
    
    # Test 5: Vector Search with Different Thresholds
    logger.info("\n🔍 Test 5: Vector Search Performance")
    
    thresholds = [0.1, 0.15, 0.2, 0.3]
    for threshold in thresholds:
        results = vector_service.search_similar_messages(test_query, conversation_id, k=3, min_score=threshold)
        logger.info(f"   Threshold {threshold}: {len(results)} results")
        if results:
            logger.info(f"     Top result score: {results[0]['score']:.3f}")
    
    # Test 6: Analytics
    logger.info("\n📈 Test 6: Analytics")
    vector_stats = rag_service.get_vector_stats()
    search_analytics = rag_service.get_search_analytics()
    
    logger.info(f"✅ Vector Stats: {vector_stats}")
    logger.info(f"✅ Search Analytics: {search_analytics}")
    
    logger.info("\n🎉 Improved RAG Test Completed!")

if __name__ == "__main__":
    test_improved_rag()
