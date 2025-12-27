"""LLM Service for AI-powered analytics"""
from dotenv import load_dotenv
import os
import json
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Import OpenAI for LLM calls
import asyncio
import openai
import re

class LLMService:
    def __init__(self):
        # Prefer OpenAI if available, otherwise fall back to Gemini
        self.api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('GEMINI_API_KEY')
        self.provider = "openai" if os.environ.get('OPENAI_API_KEY') else ("gemini" if os.environ.get('GEMINI_API_KEY') else None)
        self.model = "gpt-5-mini" if self.provider == "openai" else "gemini-2.5-flash"
        
        if not self.api_key:
            raise ValueError("No API key found in environment. Set OPENAI_API_KEY or GEMINI_API_KEY in your .env file.")

        if self.provider == "openai":
            openai.api_key = self.api_key
        
        logger.info(f"Using LLM provider: {self.provider} with model: {self.model}")

    async def _chat(self, system_message: str, user_text: str) -> str:
        """Simple async wrapper around OpenAI ChatCompletion (synchronous client via asyncio.to_thread).
        Falls back to a basic local implementation if the provider is not available or not implemented."""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_text},
        ]

        if self.provider == "openai":
            try:
                # Use blocking request in a thread to avoid blocking the event loop
                resp = await asyncio.to_thread(
                    openai.ChatCompletion.create,
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=800,
                )
                content = resp.choices[0].message.get("content", "")
                return content
            except Exception as e:
                logger.error(f"OpenAI LLM call failed: {e}", exc_info=True)
                raise
        elif self.provider == "gemini":
            # Gemini provider (Google) not implemented in this module – fallback will be used by callers
            raise NotImplementedError("Gemini provider is not implemented in this runtime. Use OPENAI_API_KEY for local development or implement Gemini support.")
        else:
            raise NotImplementedError("No supported LLM provider configured.")

    # --------- Local fallback implementations (used when remote LLM not available) ---------
    def _fallback_classify_intent(self, question: str) -> dict:
        q = question.lower()
        intent = "general"
        metrics = []
        time_period = None
        product_name = None

        # Intent heuristics
        if any(w in q for w in ["top", "bestselling", "best selling", "top 5", "top 10"]):
            intent = "sales"
            metrics.append("top_products")
        elif any(w in q for w in ["inventory", "stock", "reorder", "out of stock"]):
            intent = "inventory"
            metrics.append("inventory_levels")
        elif any(w in q for w in ["repeat", "repeat customers", "top customers", "customers"]):
            intent = "customers"
            metrics.append("repeat_customers")

        # Time period extraction (simple)
        m = re.search(r"last (\d+) days", q)
        if m:
            time_period = f"last {m.group(1)} days"
        elif "last week" in q:
            time_period = "last 7 days"
        elif "last month" in q or "30 days" in q:
            time_period = "last 30 days"

        # Product extraction (very basic)
        m = re.search(r"product\s+([\w\- ]{2,40})", question, re.IGNORECASE)
        if m:
            product_name = m.group(1).strip()

        return {
            "intent": intent,
            "time_period": time_period,
            "product_name": product_name,
            "metrics": metrics,
            "confidence": "medium"
        }

    def _fallback_generate_shopifyql(self, question: str, intent_data: dict) -> dict:
        intent = intent_data.get("intent", "general")
        time_period = intent_data.get("time_period")
        where_clause = ""
        if time_period:
            # map to days
            if "7" in time_period:
                days = 7
            elif "30" in time_period:
                days = 30
            else:
                m = re.search(r"(\d+)", time_period)
                days = int(m.group(1)) if m else 30
            where_clause = f" WHERE created_at >= DATE_SUB(NOW(), INTERVAL {days} DAY)"

        if intent == "sales":
            query = f"SELECT product_title, SUM(quantity) AS units_sold FROM line_items{where_clause} GROUP BY product_title ORDER BY units_sold DESC LIMIT 5"
            return {
                "query": query,
                "explanation": "Top selling products in the given time period",
                "data_source": "orders",
                "requires_calculation": False
            }
        elif intent == "inventory":
            query = "SELECT product_title, inventory_quantity FROM products WHERE inventory_quantity < 10 ORDER BY inventory_quantity ASC"
            return {
                "query": query,
                "explanation": "Products with low inventory levels",
                "data_source": "products",
                "requires_calculation": False
            }
        elif intent == "customers":
            query = "SELECT customer_email, COUNT(*) AS order_count FROM orders GROUP BY customer_email HAVING order_count > 1"
            return {
                "query": query,
                "explanation": "Customers with repeat orders",
                "data_source": "orders",
                "requires_calculation": False
            }
        else:
            return {
                "query": "SELECT * FROM orders LIMIT 10",
                "explanation": "Default query because intent could not be determined",
                "data_source": "orders",
                "requires_calculation": False
            }

    def _fallback_explain_results(self, question: str, query_data: dict, results: list, intent_data: dict) -> dict:
        if not results:
            return {
                "answer": "No results were returned for the query.",
                "confidence": "low",
                "recommendation": None
            }

        # Simple formatting
        if intent_data.get("intent") == "sales":
            lines = [f"{r.get('product_title', 'Unknown')} ({r.get('units_sold', r.get('quantity', 'N/A'))} units)" for r in results[:5]]
            answer = "Based on the queried period, top products are: " + ", ".join(lines)
            recommendation = "Consider restocking the top sellers if inventory is low."
            return {"answer": answer, "confidence": "medium", "recommendation": recommendation}

        # Generic table summarization
        answer = f"Returned {len(results)} rows. Example: {json.dumps(results[:3])}"
        return {"answer": answer, "confidence": "medium", "recommendation": None}
    
    async def classify_intent(self, question: str) -> dict:
        """Classify the intent of the user's question"""
        system_message = """You are an expert at analyzing Shopify analytics questions.
Your job is to classify the intent of questions into categories:
- inventory: questions about stock levels, reordering, stockouts
- sales: questions about revenue, top products, sales trends
- customers: questions about customer behavior, repeat orders
- general: other questions

Also extract:
- time_period: any time reference (last week, next month, 30 days, etc.)
- product_name: specific product mentioned
- metrics: what needs to be measured

Respond ONLY with valid JSON in this exact format:
{
  "intent": "inventory|sales|customers|general",
  "time_period": "extracted time period or null",
  "product_name": "product name or null",
  "metrics": ["list of metrics"],
  "confidence": "high|medium|low"
}"""
        
        try:
            response = await self._chat(system_message=system_message, user_text=f"Classify this question: {question}")
            # Parse JSON response
            intent_data = json.loads(response)
            return intent_data
        except NotImplementedError as e:
            logger.warning(f"LLM provider not implemented: {e}. Using local fallback classifier.")
            return self._fallback_classify_intent(question)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse intent response: {response}")
            return self._fallback_classify_intent(question)
        except Exception as e:
            logger.error(f"LLM classify_intent call failed: {e}", exc_info=True)
            return self._fallback_classify_intent(question)
    
    async def generate_shopifyql(self, question: str, intent_data: dict, store_data: dict) -> dict:
        """Generate ShopifyQL query based on intent"""
        system_message = """You are a ShopifyQL expert. Generate valid ShopifyQL queries.

ShopifyQL Query Examples:

For Sales:
- SELECT SUM(total_price) AS total_sales FROM orders WHERE created_at >= '2024-01-01'
- SELECT product_title, SUM(quantity) AS units_sold FROM line_items GROUP BY product_title ORDER BY units_sold DESC LIMIT 5
- SELECT DATE(created_at) AS sale_date, SUM(total_price) FROM orders GROUP BY sale_date

For Inventory:
- SELECT product_title, inventory_quantity FROM products WHERE inventory_quantity < 10
- SELECT product_title, inventory_quantity FROM products ORDER BY inventory_quantity ASC

For Customers:
- SELECT customer_email, COUNT(*) AS order_count FROM orders GROUP BY customer_email HAVING order_count > 1
- SELECT customer_email, SUM(total_price) AS lifetime_value FROM orders GROUP BY customer_email ORDER BY lifetime_value DESC

Respond ONLY with valid JSON:
{
  "query": "the ShopifyQL query",
  "explanation": "what this query does",
  "data_source": "orders|products|inventory|customers",
  "requires_calculation": true/false
}"""
        
        context = f"""Question: {question}
Intent: {intent_data['intent']}
Time Period: {intent_data.get('time_period', 'not specified')}
Product: {intent_data.get('product_name', 'not specified')}
Metrics: {', '.join(intent_data.get('metrics', []))}

Generate a ShopifyQL query to answer this question."""
        
        try:
            response = await self._chat(system_message=system_message, user_text=context)
            query_data = json.loads(response)
            return query_data
        except NotImplementedError as e:
            logger.warning(f"LLM provider not implemented: {e}. Using local fallback for ShopifyQL generation.")
            return self._fallback_generate_shopifyql(question, intent_data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse ShopifyQL response: {response}")
            return self._fallback_generate_shopifyql(question, intent_data)
        except Exception as e:
            logger.error(f"LLM shopifyql generation failed: {e}", exc_info=True)
            return self._fallback_generate_shopifyql(question, intent_data)
    
    async def explain_results(self, question: str, query_data: dict, results: list, intent_data: dict) -> dict:
        """Convert technical results into business-friendly language"""
        system_message = """You are a business analyst explaining data insights.
Convert technical query results into clear, actionable business language.
Provide specific numbers and recommendations.
Keep it concise and friendly.

Respond with valid JSON:
{
  "answer": "business-friendly explanation with specific numbers",
  "confidence": "high|medium|low",
  "recommendation": "optional actionable recommendation"
}"""
        
        context = f"""Original Question: {question}

Query Executed: {query_data.get('query', 'N/A')}
Query Explanation: {query_data.get('explanation', 'N/A')}

Results: {json.dumps(results[:10], indent=2)}

Explain these results in simple business terms."""
        
        try:
            response = await self._chat(system_message=system_message, user_text=context)
            explanation = json.loads(response)
            return explanation
        except NotImplementedError as e:
            logger.warning(f"LLM provider not implemented: {e}. Using local fallback to explain results.")
            return self._fallback_explain_results(question, query_data, results, intent_data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse explanation response: {response}")
            # Extract just the text if JSON parsing fails
            return {
                "answer": response,
                "confidence": intent_data.get('confidence', 'medium'),
                "recommendation": None
            }
        except Exception as e:
            logger.error(f"LLM explain_results failed: {e}", exc_info=True)
            return self._fallback_explain_results(question, query_data, results, intent_data)
