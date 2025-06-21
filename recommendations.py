import json
import asyncio
from typing import List, Dict, Optional
from config import Config
from database.models import db

# Try to import OpenAI, but handle if not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class AIRecommendationEngine:
    def __init__(self):
        if Config.AI_ENABLED and OPENAI_AVAILABLE:
            openai.api_key = Config.OPENAI_API_KEY
    
    async def generate_product_suggestions(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Generate personalized product suggestions for user"""
        if not Config.AI_ENABLED or not OPENAI_AVAILABLE:
            return await self._fallback_recommendations(user_id, limit)
        
        try:
            # Get user's order history
            user_history = await self._get_user_history(user_id)
            
            # Get popular products
            popular_products = await self._get_popular_products()
            
            # Create prompt for AI
            prompt = self._create_recommendation_prompt(user_history, popular_products)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a product recommendation AI for an Uzbek delivery service."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse AI response
            recommendations = self._parse_ai_response(response.choices[0].message.content)
            
            # Store recommendations in database
            await self._store_recommendations(user_id, recommendations, "ai_generated")
            
            return recommendations
            
        except Exception as e:
            print(f"AI recommendation error: {e}")
            return await self._fallback_recommendations(user_id, limit)
    
    async def analyze_sales_trends(self) -> Dict:
        """Analyze sales trends and provide insights"""
        if not Config.AI_ENABLED or not OPENAI_AVAILABLE:
            return {"status": "AI disabled", "trends": []}
        
        try:
            # Get sales data
            sales_data = await self._get_sales_data()
            
            prompt = f"""
            Analyze the following sales data and provide insights:
            {json.dumps(sales_data, indent=2)}
            
            Please provide:
            1. Top selling products
            2. Sales trends
            3. Recommendations for inventory
            4. Marketing suggestions
            
            Format response as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business analyst AI."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Sales analysis error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def recommend_promo_campaign(self, target_segment: str = "all") -> Dict:
        """Recommend promotional campaigns"""
        if not Config.AI_ENABLED or not OPENAI_AVAILABLE:
            return {"status": "AI disabled"}
        
        try:
            # Get user segments and product data
            segment_data = await self._get_user_segments()
            product_data = await self._get_product_performance()
            
            prompt = f"""
            Create a promotional campaign recommendation for target segment: {target_segment}
            
            User segments: {json.dumps(segment_data, indent=2)}
            Product performance: {json.dumps(product_data, indent=2)}
            
            Provide:
            1. Campaign theme
            2. Target products
            3. Discount strategy
            4. Marketing message (in Uzbek and Russian)
            5. Duration recommendation
            
            Format as JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a marketing strategist AI for Uzbek market."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Promo campaign error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def segment_users(self) -> Dict:
        """Segment users based on behavior"""
        async with db.get_connection() as conn:
            # Get user behavior data
            cursor = await conn.execute('''
                SELECT 
                    u.telegram_id,
                    u.created_at,
                    COUNT(o.id) as order_count,
                    COALESCE(SUM(o.total_amount), 0) as total_spent,
                    MAX(o.created_at) as last_order_date
                FROM users u
                LEFT JOIN orders o ON u.telegram_id = o.user_id
                WHERE u.role = 'customer'
                GROUP BY u.telegram_id
            ''')
            
            users = await cursor.fetchall()
            
            segments = {
                "vip": [],      # High value customers
                "active": [],   # Regular customers
                "inactive": [], # Haven't ordered recently
                "new": []       # New users
            }
            
            for user in users:
                user_dict = dict(user)
                
                if user_dict['total_spent'] > 100000:  # 100k som
                    segments["vip"].append(user_dict['telegram_id'])
                elif user_dict['order_count'] >= 3:
                    segments["active"].append(user_dict['telegram_id'])
                elif user_dict['order_count'] == 0:
                    segments["new"].append(user_dict['telegram_id'])
                else:
                    segments["inactive"].append(user_dict['telegram_id'])
            
            return segments
    
    async def _get_user_history(self, user_id: int) -> List[Dict]:
        """Get user's order history"""
        async with db.get_connection() as conn:
            cursor = await conn.execute('''
                SELECT 
                    p.name_uz, p.name_ru, p.price, oi.quantity,
                    o.created_at, c.name_uz as category_uz, c.name_ru as category_ru
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                JOIN products p ON oi.product_id = p.id
                JOIN categories c ON p.category_id = c.id
                WHERE o.user_id = ?
                ORDER BY o.created_at DESC
                LIMIT 20
            ''', (user_id,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def _get_popular_products(self, limit: int = 10) -> List[Dict]:
        """Get popular products"""
        async with db.get_connection() as conn:
            cursor = await conn.execute('''
                SELECT 
                    p.id, p.name_uz, p.name_ru, p.price,
                    COUNT(oi.id) as order_count,
                    c.name_uz as category_uz, c.name_ru as category_ru
                FROM products p
                LEFT JOIN order_items oi ON p.id = oi.product_id
                JOIN categories c ON p.category_id = c.id
                WHERE p.is_available = 1
                GROUP BY p.id
                ORDER BY order_count DESC
                LIMIT ?
            ''', (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def _fallback_recommendations(self, user_id: int, limit: int) -> List[Dict]:
        """Fallback recommendations when AI is not available"""
        # Simple rule-based recommendations
        popular_products = await self._get_popular_products(limit)
        
        recommendations = []
        for product in popular_products:
            recommendations.append({
                "product_id": product['id'],
                "name_uz": product['name_uz'],
                "name_ru": product['name_ru'],
                "price": product['price'],
                "reason": "Популярный товар",
                "confidence": 0.7
            })
        
        return recommendations
    
    def _create_recommendation_prompt(self, user_history: List[Dict], popular_products: List[Dict]) -> str:
        """Create prompt for AI recommendations"""
        return f"""
        Based on this user's order history and popular products, recommend 5 products:
        
        User History:
        {json.dumps(user_history, indent=2)}
        
        Popular Products:
        {json.dumps(popular_products, indent=2)}
        
        Provide recommendations in JSON format with product_id, reason, and confidence score.
        Consider user preferences, seasonal trends, and complementary products.
        """
    
    def _parse_ai_response(self, response: str) -> List[Dict]:
        """Parse AI response into structured recommendations"""
        try:
            return json.loads(response)
        except:
            # Fallback parsing
            return []
    
    async def _store_recommendations(self, user_id: int, recommendations: List[Dict], rec_type: str):
        """Store recommendations in database"""
        async with db.get_connection() as conn:
            for rec in recommendations:
                await conn.execute('''
                    INSERT INTO ai_recommendations 
                    (user_id, product_id, recommendation_type, confidence_score)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_id, 
                    rec.get('product_id'), 
                    rec_type, 
                    rec.get('confidence', 0.5)
                ))
            await conn.commit()
    
    async def _get_sales_data(self) -> Dict:
        """Get sales data for analysis"""
        async with db.get_connection() as conn:
            cursor = await conn.execute('''
                SELECT 
                    DATE(o.created_at) as date,
                    COUNT(o.id) as order_count,
                    SUM(o.total_amount) as revenue,
                    p.name_uz as product_name,
                    SUM(oi.quantity) as quantity_sold
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN products p ON oi.product_id = p.id
                WHERE o.created_at >= date('now', '-30 days')
                GROUP BY DATE(o.created_at), p.id
                ORDER BY date DESC
            ''')
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def _get_user_segments(self) -> Dict:
        """Get user segment data"""
        segments = await self.segment_users()
        return {
            "total_users": sum(len(segment) for segment in segments.values()),
            "segments": segments
        }
    
    async def _get_product_performance(self) -> List[Dict]:
        """Get product performance data"""
        async with db.get_connection() as conn:
            cursor = await conn.execute('''
                SELECT 
                    p.id, p.name_uz, p.price,
                    COUNT(oi.id) as times_ordered,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.quantity * oi.price) as total_revenue
                FROM products p
                LEFT JOIN order_items oi ON p.id = oi.product_id
                GROUP BY p.id
                ORDER BY total_revenue DESC
            ''')
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# Initialize AI engine
ai_engine = AIRecommendationEngine()