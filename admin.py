from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database.models import db
from config import Config
from keyboards.keyboards import (
    get_admin_menu_keyboard, get_categories_management_keyboard,
    get_products_management_keyboard, get_orders_management_keyboard
)
from localization.texts import get_text
from ai.recommendations import ai_engine

router = Router()

class AdminStates(StatesGroup):
    waiting_for_category_name_uz = State()
    waiting_for_category_name_ru = State()
    waiting_for_category_description_uz = State()
    waiting_for_category_description_ru = State()
    waiting_for_product_name_uz = State()
    waiting_for_product_name_ru = State()
    waiting_for_product_description_uz = State()
    waiting_for_product_description_ru = State()
    waiting_for_product_price = State()
    waiting_for_product_category = State()

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in Config.ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Show admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    await message.answer(
        "🔧 **Панель администратора**\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Show bot statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    async with db.get_connection() as conn:
        # Get user statistics
        cursor = await conn.execute('SELECT COUNT(*) FROM users')
        total_users = (await cursor.fetchone())[0]
        
        cursor = await conn.execute('SELECT COUNT(*) FROM users WHERE created_at >= date("now", "-7 days")')
        new_users_week = (await cursor.fetchone())[0]
        
        # Get order statistics
        cursor = await conn.execute('SELECT COUNT(*) FROM orders')
        total_orders = (await cursor.fetchone())[0]
        
        cursor = await conn.execute('SELECT COUNT(*) FROM orders WHERE created_at >= date("now", "-7 days")')
        orders_week = (await cursor.fetchone())[0]
        
        cursor = await conn.execute('SELECT SUM(total_amount) FROM orders WHERE payment_status = "completed"')
        total_revenue = (await cursor.fetchone())[0] or 0
        
        # Get product statistics
        cursor = await conn.execute('SELECT COUNT(*) FROM products WHERE is_available = 1')
        active_products = (await cursor.fetchone())[0]
    
    stats_text = f"""📊 **Статистика бота**

👥 **Пользователи:**
• Всего: {total_users}
• Новых за неделю: {new_users_week}

📋 **Заказы:**
• Всего: {total_orders}
• За неделю: {orders_week}

💰 **Доходы:**
• Общий доход: {total_revenue:,} сум

📦 **Товары:**
• Активных товаров: {active_products}
"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_menu_keyboard(),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "admin_orders")
async def manage_orders(callback: CallbackQuery):
    """Manage orders"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    async with db.get_connection() as conn:
        cursor = await conn.execute('''
            SELECT o.id, o.user_id, o.total_amount, o.order_status, o.created_at,
                   u.first_name, u.phone
            FROM orders o
            JOIN users u ON o.user_id = u.telegram_id
            WHERE o.order_status IN ('new', 'confirmed', 'preparing')
            ORDER BY o.created_at DESC
            LIMIT 10
        ''')
        orders = await cursor.fetchall()
    
    if not orders:
        await callback.message.edit_text(
            "📋 Нет активных заказов",
            reply_markup=get_admin_menu_keyboard()
        )
        return
    
    orders_text = "📋 **Активные заказы:**\n\n"
    for order in orders:
        orders_text += f"🆔 Заказ #{order[0]}\n"
        orders_text += f"👤 {order[5]} ({order[6]})\n"
        orders_text += f"💰 {order[2]:,} сум\n"
        orders_text += f"📊 Статус: {order[3]}\n"
        orders_text += f"📅 {order[4]}\n\n"
    
    await callback.message.edit_text(
        orders_text,
        reply_markup=get_orders_management_keyboard(),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "admin_products")
async def manage_products(callback: CallbackQuery):
    """Manage products"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    await callback.message.edit_text(
        "📦 **Управление товарами**\n\nВыберите действие:",
        reply_markup=get_products_management_keyboard(),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "admin_categories")
async def manage_categories(callback: CallbackQuery):
    """Manage categories"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    await callback.message.edit_text(
        "📂 **Управление категориями**\n\nВыберите действие:",
        reply_markup=get_categories_management_keyboard(),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "admin_ai_insights")
async def show_ai_insights(callback: CallbackQuery):
    """Show AI insights"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    await callback.answer("🤖 Генерирую AI-аналитику...")
    
    try:
        # Get AI insights
        trends = await ai_engine.analyze_sales_trends()
        segments = await ai_engine.segment_users()
        promo_campaign = await ai_engine.recommend_promo_campaign()
        
        insights_text = "🤖 **AI Аналитика**\n\n"
        
        if trends.get('status') != 'error':
            insights_text += "📈 **Тренды продаж:**\n"
            if 'top_products' in trends:
                for product in trends['top_products'][:3]:
                    insights_text += f"• {product.get('name', 'N/A')}\n"
            insights_text += "\n"
        
        insights_text += f"👥 **Сегменты пользователей:**\n"
        insights_text += f"• VIP: {len(segments.get('vip', []))}\n"
        insights_text += f"• Активные: {len(segments.get('active', []))}\n"
        insights_text += f"• Неактивные: {len(segments.get('inactive', []))}\n"
        insights_text += f"• Новые: {len(segments.get('new', []))}\n\n"
        
        if promo_campaign.get('status') != 'error':
            insights_text += "🎪 **Рекомендуемая акция:**\n"
            insights_text += f"• Тема: {promo_campaign.get('theme', 'N/A')}\n"
            insights_text += f"• Скидка: {promo_campaign.get('discount', 'N/A')}\n"
        
        await callback.message.edit_text(
            insights_text,
            reply_markup=get_admin_menu_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка получения AI-аналитики: {str(e)}",
            reply_markup=get_admin_menu_keyboard()
        )

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Back to admin menu"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа")
        return
    
    await callback.message.edit_text(
        "🔧 **Панель администратора**\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode='Markdown'
    )