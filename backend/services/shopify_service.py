"""Shopify Service - handles Shopify API interactions (mocked for now)"""
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class ShopifyService:
    """Service to interact with Shopify API (currently using mock data)"""
    
    def __init__(self, store_id: str):
        self.store_id = store_id
        self.mock_data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> dict:
        """Generate realistic mock Shopify data"""
        products = [
            {"id": 1, "title": "Wireless Headphones", "inventory_quantity": 45, "price": 79.99},
            {"id": 2, "title": "Smart Watch", "inventory_quantity": 12, "price": 199.99},
            {"id": 3, "title": "Phone Case", "inventory_quantity": 8, "price": 14.99},
            {"id": 4, "title": "Laptop Stand", "inventory_quantity": 25, "price": 49.99},
            {"id": 5, "title": "USB-C Cable", "inventory_quantity": 150, "price": 9.99},
            {"id": 6, "title": "Bluetooth Speaker", "inventory_quantity": 5, "price": 89.99},
            {"id": 7, "title": "Portable Charger", "inventory_quantity": 3, "price": 39.99},
            {"id": 8, "title": "Wireless Mouse", "inventory_quantity": 60, "price": 29.99},
            {"id": 9, "title": "Keyboard", "inventory_quantity": 18, "price": 69.99},
            {"id": 10, "title": "Monitor", "inventory_quantity": 7, "price": 299.99},
        ]
        
        # Generate orders for last 90 days
        orders = []
        customers = [
            "customer1@example.com", "customer2@example.com", "customer3@example.com",
            "customer4@example.com", "customer5@example.com"
        ]
        
        for i in range(200):  # 200 orders
            days_ago = random.randint(0, 90)
            order_date = datetime.now() - timedelta(days=days_ago)
            product = random.choice(products)
            quantity = random.randint(1, 5)
            
            orders.append({
                "id": i + 1,
                "created_at": order_date.isoformat(),
                "customer_email": random.choice(customers),
                "product_title": product["title"],
                "product_id": product["id"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": product["price"] * quantity,
                "status": "completed"
            })
        
        return {
            "products": products,
            "orders": orders
        }
    
    async def execute_query(self, query_data: dict) -> list:
        """Execute ShopifyQL query (simulated)"""
        data_source = query_data.get('data_source', 'orders')
        query = query_data.get('query', '').lower()
        
        logger.info(f"Executing query on {data_source}: {query}")
        
        # Simulate query execution based on patterns
        if 'inventory' in query or data_source == 'products':
            return self._query_products(query)
        elif 'customer' in query:
            return self._query_customers(query)
        else:
            return self._query_orders(query)
    
    def _query_products(self, query: str) -> list:
        """Query product/inventory data"""
        products = self.mock_data['products']
        
        # Low stock query
        if 'inventory_quantity < 10' in query or 'stockout' in query or 'out of stock' in query:
            return [p for p in products if p['inventory_quantity'] < 10]
        
        # All products sorted by inventory
        if 'order by inventory_quantity' in query:
            return sorted(products, key=lambda x: x['inventory_quantity'])
        
        return products
    
    def _query_orders(self, query: str) -> list:
        """Query order data"""
        orders = self.mock_data['orders']
        
        # Last 7 days
        if 'last week' in query or '7 days' in query:
            cutoff = datetime.now() - timedelta(days=7)
            filtered = [o for o in orders if datetime.fromisoformat(o['created_at']) >= cutoff]
        # Last 30 days
        elif 'last 30 days' in query or 'last month' in query:
            cutoff = datetime.now() - timedelta(days=30)
            filtered = [o for o in orders if datetime.fromisoformat(o['created_at']) >= cutoff]
        else:
            filtered = orders
        
        # Top selling products
        if 'group by product_title' in query or 'top' in query:
            product_sales = {}
            for order in filtered:
                product = order['product_title']
                if product not in product_sales:
                    product_sales[product] = {'product_title': product, 'units_sold': 0, 'revenue': 0}
                product_sales[product]['units_sold'] += order['quantity']
                product_sales[product]['revenue'] += order['total_price']
            
            result = list(product_sales.values())
            result.sort(key=lambda x: x['units_sold'], reverse=True)
            
            # Return top 5 if specified
            if 'limit 5' in query or 'top 5' in query:
                return result[:5]
            return result
        
        # Total sales
        if 'sum(total_price)' in query:
            total = sum(o['total_price'] for o in filtered)
            return [{'total_sales': round(total, 2), 'order_count': len(filtered)}]
        
        return filtered[:20]  # Return sample
    
    def _query_customers(self, query: str) -> list:
        """Query customer data"""
        orders = self.mock_data['orders']
        
        # Repeat customers
        if 'having order_count > 1' in query or 'repeat' in query:
            customer_orders = {}
            for order in orders:
                email = order['customer_email']
                if email not in customer_orders:
                    customer_orders[email] = {'customer_email': email, 'order_count': 0, 'total_spent': 0}
                customer_orders[email]['order_count'] += 1
                customer_orders[email]['total_spent'] += order['total_price']
            
            # Filter repeat customers
            repeat = [c for c in customer_orders.values() if c['order_count'] > 1]
            repeat.sort(key=lambda x: x['order_count'], reverse=True)
            return repeat
        
        return []
    
    def get_store_context(self) -> dict:
        """Get store context for AI agent"""
        return {
            "store_id": self.store_id,
            "product_count": len(self.mock_data['products']),
            "order_count": len(self.mock_data['orders']),
            "using_mock_data": True
        }
