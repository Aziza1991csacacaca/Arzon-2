from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import db
from keyboards.keyboards import get_profile_keyboard, get_main_menu_keyboard
from localization.texts import get_text

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()

@router.message(F.text.in_(['👤 Профил', '👤 Профиль']))
async def show_profile(message: Message):
    """Show user profile"""
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    lang = user.get('language_code', 'uz')
    
    # Get user statistics
    async with db.get_connection() as conn:
        cursor = await conn.execute(
            'SELECT COUNT(*) FROM orders WHERE user_id = ?',
            (message.from_user.id,)
        )
        order_count = (await cursor.fetchone())[0]
        
        cursor = await conn.execute(
            'SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE user_id = ? AND payment_status = "completed"',
            (message.from_user.id,)
        )
        total_spent = (await cursor.fetchone())[0]
    
    profile_text = get_text('profile_info', lang).format(
        user.get('first_name', 'N/A'),
        user.get('phone', get_text('not_set', lang)),
        user.get('address', get_text('not_set', lang)),
        order_count,
        f"{total_spent:,}",
        f"{user.get('bonus_balance', 0):,}",
        user.get('referral_code', 'N/A')
    )
    
    await message.answer(
        profile_text,
        reply_markup=get_profile_keyboard(lang),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "edit_phone")
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    """Edit phone number"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    await callback.message.edit_text(
        get_text('enter_new_phone', lang),
        reply_markup=None
    )
    
    await state.set_state(ProfileStates.waiting_for_phone)

@router.message(ProfileStates.waiting_for_phone, F.text)
async def phone_updated(message: Message, state: FSMContext):
    """Handle phone update"""
    user = await db.get_user(message.from_user.id)
    lang = user.get('language_code', 'uz')
    
    phone = message.text
    await db.update_user_profile(message.from_user.id, phone=phone)
    
    await message.answer(
        get_text('phone_updated', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    await state.clear()

@router.callback_query(F.data == "edit_address")
async def edit_address(callback: CallbackQuery, state: FSMContext):
    """Edit address"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    await callback.message.edit_text(
        get_text('enter_new_address', lang),
        reply_markup=None
    )
    
    await state.set_state(ProfileStates.waiting_for_address)

@router.message(ProfileStates.waiting_for_address, F.text)
async def address_updated(message: Message, state: FSMContext):
    """Handle address update"""
    user = await db.get_user(message.from_user.id)
    lang = user.get('language_code', 'uz')
    
    address = message.text
    await db.update_user_profile(message.from_user.id, address=address)
    
    await message.answer(
        get_text('address_updated', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    await state.clear()

@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: CallbackQuery):
    """Show user's orders"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    async with db.get_connection() as conn:
        cursor = await conn.execute('''
            SELECT id, total_amount, order_status, created_at, delivery_address
            FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (callback.from_user.id,))
        orders = await cursor.fetchall()
    
    if not orders:
        await callback.message.edit_text(
            get_text('no_orders', lang),
            reply_markup=get_profile_keyboard(lang)
        )
        return
    
    orders_text = get_text('my_orders_list', lang) + "\n\n"
    
    for order in orders:
        status_emoji = {
            'new': '🆕',
            'confirmed': '✅',
            'preparing': '👨‍🍳',
            'delivering': '🚚',
            'completed': '✅',
            'cancelled': '❌'
        }.get(order[2], '❓')
        
        orders_text += f"{status_emoji} **Заказ #{order[0]}**\n"
        orders_text += f"💰 {order[1]:,} сум\n"
        orders_text += f"📍 {order[4]}\n"
        orders_text += f"📅 {order[3]}\n\n"
    
    await callback.message.edit_text(
        orders_text,
        reply_markup=get_profile_keyboard(lang),
        parse_mode='Markdown'
    )