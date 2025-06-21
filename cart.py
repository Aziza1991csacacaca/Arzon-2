from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import db
from keyboards.keyboards import (
    get_cart_keyboard, get_payment_keyboard, 
    get_location_keyboard, get_main_menu_keyboard
)
from localization.texts import get_text

router = Router()

class OrderStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_payment = State()

@router.message(F.text.in_(['🛒 Саватча', '🛒 Корзина']))
async def show_cart(message: Message):
    """Show user's cart"""
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    lang = user.get('language_code', 'uz')
    cart_items = await db.get_cart(message.from_user.id)
    
    if not cart_items:
        await message.answer(
            get_text('cart_empty', lang),
            reply_markup=get_main_menu_keyboard(lang)
        )
        return
    
    # Calculate total and format cart
    total = 0
    cart_text = "🛒 **Саватчангиз:**\n\n"
    
    for item in cart_items:
        name = item[f'name_{lang}'] if f'name_{lang}' in item else item['name_uz']
        item_total = item['price'] * item['quantity']
        total += item_total
        
        cart_text += f"📦 {name}\n"
        cart_text += f"   {get_text('quantity', lang).format(item['quantity'])}\n"
        cart_text += f"   💰 {item_total:,} сўм\n\n"
    
    cart_text += f"**{get_text('cart_total', lang).format(f'{total:,}')}**"
    
    await message.answer(
        cart_text,
        reply_markup=get_cart_keyboard(lang),
        parse_mode='Markdown'
    )

@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Start checkout process"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    # Check if user has address
    if not user.get('address'):
        await callback.message.edit_text(
            "📍 Илтимос, етказиб бериш манзилини юборинг:",
            reply_markup=None
        )
        await callback.message.answer(
            "📍 Локацияни юборинг:",
            reply_markup=get_location_keyboard(lang)
        )
        await state.set_state(OrderStates.waiting_for_location)
    else:
        # Proceed to payment
        await callback.message.edit_text(
            get_text('choose_payment', lang),
            reply_markup=get_payment_keyboard(lang)
        )
        await state.set_state(OrderStates.waiting_for_payment)

@router.message(OrderStates.waiting_for_location, F.location)
async def location_received(message: Message, state: FSMContext):
    """Handle location for delivery"""
    user = await db.get_user(message.from_user.id)
    lang = user.get('language_code', 'uz')
    
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    await state.update_data(
        latitude=latitude,
        longitude=longitude
    )
    
    await message.answer(
        get_text('location_received', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    await message.answer(
        get_text('choose_payment', lang),
        reply_markup=get_payment_keyboard(lang)
    )
    
    await state.set_state(OrderStates.waiting_for_payment)

@router.callback_query(F.data.startswith("payment_"), OrderStates.waiting_for_payment)
async def payment_selected(callback: CallbackQuery, state: FSMContext):
    """Handle payment method selection"""
    payment_method = callback.data.split("_")[1]
    
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    # Get cart items and calculate total
    cart_items = await db.get_cart(callback.from_user.id)
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Get location data
    data = await state.get_data()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # Create order
    order_id = await db.create_order(
        user_id=callback.from_user.id,
        total_amount=total,
        delivery_address=user.get('address', 'Локация орқали'),
        phone=user.get('phone'),
        payment_method=payment_method,
        latitude=latitude,
        longitude=longitude
    )
    
    await callback.message.edit_text(
        get_text('order_created', lang).format(order_id),
        reply_markup=None
    )
    
    await callback.message.answer(
        get_text('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    
    await state.clear()

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear user's cart"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    await db.clear_cart(callback.from_user.id)
    
    await callback.message.edit_text(
        get_text('cart_empty', lang),
        reply_markup=None
    )
    
    await callback.message.answer(
        get_text('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )