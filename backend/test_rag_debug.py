#!/usr/bin/env python3
"""
RAG Debug Script - Focused testing of conversation-specific search
"""

import logging
from services.vector_service import VectorService
from services.database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_conversation_search():
    """Debug conversation-specific search functionality"""
    
    vector_service = VectorService()
    database_service = DatabaseService()
    
    # Get all conversations
    conversations = database_service.get_all_conversations()
    logger.info(f"Found {len(conversations)} conversations")
    
    if not conversations:
        logger.error("No conversations found!")
        return
    
    # Test with the first conversation
    conversation_id = conversations[0]["id"]
    conversation_name = conversations[0]["bot_name"]
    logger.info(f"Testing conversation: {conversation_name} ({conversation_id})")
    
    # Get messages for this conversation
    messages = vector_service.get_conversation_messages(conversation_id)
    logger.info(f"Found {len(messages)} messages in conversation")
    
    if messages:
        # Show first few messages
        for i, msg in enumerate(messages[:3]):
            logger.info(f"  {i+1}. [{msg['role']}] {msg['content_preview'][:100]}...")
    
    # Test search with different thresholds
    test_query = "How do I create a function?"
    logger.info(f"\n🔍 Testing query: '{test_query}'")
    
    # Test 1: Search across all conversations
    logger.info("\n📋 Search across ALL conversations:")
    all_results = vector_service.search_similar_messages(test_query, k=5, min_score=0.1)
    logger.info(f"Found {len(all_results)} results")
    for i, result in enumerate(all_results[:3]):
        logger.info(f"  {i+1}. [{result['role']}] {result['content_preview'][:80]}... (score: {result['score']:.3f})")
    
    # Test 2: Search in specific conversation with low threshold
    logger.info(f"\n📋 Search in conversation {conversation_id} (threshold: 0.1):")
    conv_results_low = vector_service.search_similar_messages(test_query, conversation_id, k=5, min_score=0.1)
    logger.info(f"Found {len(conv_results_low)} results")
    for i, result in enumerate(conv_results_low):
        logger.info(f"  {i+1}. [{result['role']}] {result['content_preview'][:80]}... (score: {result['score']:.3f})")
    
    # Test 3: Search in specific conversation with default threshold
    logger.info(f"\n📋 Search in conversation {conversation_id} (threshold: 0.3):")
    conv_results_default = vector_service.search_similar_messages(test_query, conversation_id, k=5, min_score=0.3)
    logger.info(f"Found {len(conv_results_default)} results")
    for i, result in enumerate(conv_results_default):
        logger.info(f"  {i+1}. [{result['role']}] {result['content_preview'][:80]}... (score: {result['score']:.3f})")
    
    # Test 4: Check if conversation has the right messages
    logger.info(f"\n📋 Checking conversation messages for '{test_query}':")
    matching_messages = [msg for msg in messages if 'function' in msg['content_preview'].lower()]
    logger.info(f"Found {len(matching_messages)} messages containing 'function'")
    for i, msg in enumerate(matching_messages):
        logger.info(f"  {i+1}. [{msg['role']}] {msg['content_preview'][:80]}...")

if __name__ == "__main__":
    debug_conversation_search()
