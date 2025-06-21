import sqlite3
import aiosqlite
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

class Database:
    def __init__(self, db_path: str = "arzon_bot.db"):
        self.db_path = db_path
    
    async def get_connection(self):
        """Get database connection"""
        return aiosqlite.connect(self.db_path)
    
    async def init_db(self):
        """Initialize database with all required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    address TEXT,
                    language_code TEXT DEFAULT 'uz',
                    role TEXT DEFAULT 'customer',
                    referral_code TEXT UNIQUE,
                    referred_by TEXT,
                    bonus_balance INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_uz TEXT NOT NULL,
                    name_ru TEXT NOT NULL,
                    description_uz TEXT,
                    description_ru TEXT,
                    image_url TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Products table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    name_uz TEXT NOT NULL,
                    name_ru TEXT NOT NULL,
                    description_uz TEXT,
                    description_ru TEXT,
                    price INTEGER NOT NULL,
                    image_url TEXT,
                    is_available BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
            ''')
            
            # Orders table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    courier_id INTEGER,
                    total_amount INTEGER NOT NULL,
                    delivery_address TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    payment_method TEXT NOT NULL,
                    payment_status TEXT DEFAULT 'pending',
                    order_status TEXT DEFAULT 'new',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (courier_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # Order items table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Cart table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # AI recommendations table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ai_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_id INTEGER,
                    recommendation_type TEXT,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Referrals table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    bonus_awarded BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users (telegram_id),
                    FOREIGN KEY (referred_id) REFERENCES users (telegram_id)
                )
            ''')
            
            await db.commit()
    
    async def create_user(self, telegram_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None,
                         language_code: str = 'uz', referred_by: str = None) -> str:
        """Create new user and return referral code"""
        referral_code = str(uuid.uuid4())[:8].upper()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users 
                (telegram_id, username, first_name, last_name, language_code, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name, language_code, referral_code, referred_by))
            
            # If user was referred, create referral record
            if referred_by:
                await db.execute('''
                    INSERT INTO referrals (referrer_id, referred_id)
                    SELECT telegram_id, ? FROM users WHERE referral_code = ?
                ''', (telegram_id, referred_by))
            
            await db.commit()
        
        return referral_code
    
    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_user_profile(self, telegram_id: int, phone: str = None, address: str = None):
        """Update user profile information"""
        async with aiosqlite.connect(self.db_path) as db:
            if phone and address:
                await db.execute('''
                    UPDATE users SET phone = ?, address = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (phone, address, telegram_id))
            elif phone:
                await db.execute('''
                    UPDATE users SET phone = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (phone, telegram_id))
            elif address:
                await db.execute('''
                    UPDATE users SET address = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (address, telegram_id))
            
            await db.commit()
    
    async def get_categories(self) -> List[Dict]:
        """Get all active categories"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM categories WHERE is_active = 1 ORDER BY name_uz'
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Get products by category"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM products 
                WHERE category_id = ? AND is_available = 1 
                ORDER BY name_uz
            ''', (category_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_product(self, product_id: int) -> Optional[Dict]:
        """Get product by id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM products WHERE id = ?', (product_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        """Add product to cart"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if product already in cart
            cursor = await db.execute('''
                SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?
            ''', (user_id, product_id))
            existing = await cursor.fetchone()
            
            if existing:
                # Update quantity
                await db.execute('''
                    UPDATE cart SET quantity = quantity + ? WHERE id = ?
                ''', (quantity, existing[0]))
            else:
                # Add new item
                await db.execute('''
                    INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)
                ''', (user_id, product_id, quantity))
            
            await db.commit()
    
    async def get_cart(self, user_id: int) -> List[Dict]:
        """Get user's cart with product details"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT c.*, p.name_uz, p.name_ru, p.price, p.image_url
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
                ORDER BY c.created_at
            ''', (user_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def clear_cart(self, user_id: int):
        """Clear user's cart"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def create_order(self, user_id: int, total_amount: int, delivery_address: str,
                          phone: str, payment_method: str, latitude: float = None,
                          longitude: float = None, notes: str = None) -> int:
        """Create new order and return order_id"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO orders 
                (user_id, total_amount, delivery_address, phone, latitude, longitude, 
                 payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, total_amount, delivery_address, phone, latitude, longitude,
                  payment_method, notes))
            
            order_id = cursor.lastrowid
            
            # Move cart items to order_items
            cart_items = await self.get_cart(user_id)
            for item in cart_items:
                await db.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'], item['price']))
            
            # Clear cart
            await db.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            
            await db.commit()
            return order_id

# Initialize database instance
db = Database()