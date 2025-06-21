import asyncio
from aiogram import Bot
from typing import List, Dict, Optional
from database.models import db
from config import Config
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def notify_admins(self, message: str, parse_mode: Optional[str] = None):
        """Send notification to all admins"""
        for admin_id in Config.ADMIN_IDS:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=parse_mode
                )
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_id}: {e}")
    
    async def notify_new_order(self, order_id: int):
        """Notify admins about new order"""
        async with db.get_connection() as conn:
            cursor = await conn.execute('''
                SELECT o.*, u.first_name, u.phone
                FROM orders o
                JOIN users u ON o.user_id = u.telegram_id
                WHERE o.id = ?
            ''', (order_id,))
            order = await cursor.fetchone()
        
        if order:
            message = f"""🆕 **Новый заказ #{order[0]}**

👤 Клиент: {order[12]} ({order[13]})
💰 Сумма: {order[2]:,} сум
📍 Адрес: {order[3]}
💳 Оплата: {order[6]}
📅 Время: {order[9]}

Требует подтверждения!"""
            
            await self.notify_admins(message, parse_mode='Markdown')
    
    async def notify_order_status_change(self, order_id: int, new_status: str, user_id: int):
        """Notify customer about order status change"""
        status_messages = {
            'confirmed': '✅ Ваш заказ подтвержден и принят в работу!',
            'preparing': '👨‍🍳 Ваш заказ готовится',
            'ready': '📦 Ваш заказ готов к выдаче',
            'delivering': '🚚 Ваш заказ в пути',
            'completed': '✅ Заказ доставлен! Спасибо за покупку!',
            'cancelled': '❌ Ваш заказ отменен'
        }
        
        message = status_messages.get(new_status, f'Статус заказа изменен на: {new_status}')
        message = f"📋 **Заказ #{order_id}**\n\n{message}"
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about order status: {e}")
    
    async def notify_low_stock(self, product_id: int, current_stock: int):
        """Notify admins about low stock"""
        async with db.get_connection() as conn:
            cursor = await conn.execute(
                'SELECT name_ru FROM products WHERE id = ?',
                (product_id,)
            )
            product = await cursor.fetchone()
        
        if product:
            message = f"⚠️ **Низкий остаток товара**\n\n📦 {product[0]}\n📊 Остаток: {current_stock} шт."
            await self.notify_admins(message, parse_mode='Markdown')
    
    async def send_promotional_message(self, user_ids: List[int], message: str):
        """Send promotional message to users"""
        success_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                success_count += 1
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to send promo message to user {user_id}: {e}")
                failed_count += 1
        
        # Notify admins about campaign results
        result_message = f"""📢 **Результаты рассылки**

✅ Успешно отправлено: {success_count}
❌ Ошибок: {failed_count}
📊 Всего: {len(user_ids)}"""
        
        await self.notify_admins(result_message, parse_mode='Markdown')
    
    async def notify_referral_bonus(self, user_id: int, bonus_amount: int):
        """Notify user about referral bonus"""
        message = f"""🎉 **Поздравляем!**

Вы получили реферальный бонус: {bonus_amount:,} сум

Спасибо за приглашение друзей! 🎁"""
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about referral bonus: {e}")
    
    async def send_daily_stats(self):
        """Send daily statistics to admins"""
        async with db.get_connection() as conn:
            # Get today's statistics
            cursor = await conn.execute('''
                SELECT 
                    COUNT(*) as orders_count,
                    COALESCE(SUM(total_amount), 0) as revenue
                FROM orders 
                WHERE DATE(created_at) = DATE('now')
            ''')
            today_stats = await cursor.fetchone()
            
            cursor = await conn.execute('''
                SELECT COUNT(*) 
                FROM users 
                WHERE DATE(created_at) = DATE('now')
            ''')
            new_users = (await cursor.fetchone())[0]
        
        message = f"""📊 **Статистика за сегодня**

📋 Заказов: {today_stats[0]}
💰 Выручка: {today_stats[1]:,} сум
👥 Новых пользователей: {new_users}

📅 {datetime.now().strftime('%d.%m.%Y')}"""
        
        await self.notify_admins(message, parse_mode='Markdown')

# Global notification service instance
notification_service = None

def init_notification_service(bot: Bot):
    """Initialize notification service"""
    global notification_service
    notification_service = NotificationService(bot)
    return notification_service