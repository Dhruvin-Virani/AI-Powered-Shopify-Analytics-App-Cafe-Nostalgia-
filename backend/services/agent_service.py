"""AI Agent Service - orchestrates the complete workflow"""
import logging
from typing import Dict, Any
from .llm_service import LLMService
from .shopify_service import ShopifyService

logger = logging.getLogger(__name__)

class AgentService:
    """Main AI Agent that orchestrates the analytics workflow"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def process_question(self, store_id: str, question: str) -> Dict[str, Any]:
        """Complete agent workflow: Intent -> Query -> Execute -> Explain"""
        try:
            # Step 1: Initialize Shopify service
            shopify = ShopifyService(store_id)
            store_context = shopify.get_store_context()
            logger.info(f"Processing question for store: {store_id}")
            
            # Step 2: Classify Intent
            logger.info("Step 1: Classifying intent...")
            intent_data = await self.llm_service.classify_intent(question)
            logger.info(f"Intent classified as: {intent_data['intent']} with confidence: {intent_data['confidence']}")
            
            # Step 3: Generate ShopifyQL
            logger.info("Step 2: Generating ShopifyQL query...")
            query_data = await self.llm_service.generate_shopifyql(
                question, intent_data, store_context
            )
            logger.info(f"Generated query: {query_data['query']}")
            
            # Step 4: Execute Query
            logger.info("Step 3: Executing query against Shopify...")
            results = await shopify.execute_query(query_data)
            logger.info(f"Query returned {len(results)} results")
            
            # Step 5: Explain Results
            logger.info("Step 4: Generating business-friendly explanation...")
            explanation = await self.llm_service.explain_results(
                question, query_data, results, intent_data
            )
            
            # Prepare final response
            response = {
                "answer": explanation['answer'],
                "confidence": explanation['confidence'],
                "recommendation": explanation.get('recommendation'),
                "metadata": {
                    "intent": intent_data['intent'],
                    "query_executed": query_data['query'],
                    "data_points": len(results),
                    "store_id": store_id,
                    "using_mock_data": store_context['using_mock_data']
                }
            }
            
            logger.info("Question processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}", exc_info=True)
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "confidence": "low",
                "recommendation": None,
                "metadata": {
                    "error": str(e),
                    "store_id": store_id
                }
            }
