from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import db
from keyboards.keyboards import (
    get_language_keyboard, get_contact_keyboard, 
    get_main_menu_keyboard, get_back_keyboard
)
from localization.texts import get_text
import re

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_contact = State()
    waiting_for_address = State()
    waiting_for_referral = State()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Handle /start command"""
    user = await db.get_user(message.from_user.id)
    
    # Extract referral code from start parameter
    referral_code = None
    if message.text and len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
    
    if not user:
        # New user - show language selection
        await state.update_data(referral_code=referral_code)
        await message.answer(
            get_text('welcome'),
            reply_markup=get_language_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_language)
    else:
        # Existing user - show main menu
        lang = user.get('language_code', 'uz')
        await message.answer(
            get_text('main_menu', lang),
            reply_markup=get_main_menu_keyboard(lang)
        )

@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery, state: FSMContext):
    """Handle language selection"""
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    
    await callback.message.edit_text(
        get_text('registration_needed', lang),
        reply_markup=None
    )
    
    await callback.message.answer(
        get_text('registration_needed', lang),
        reply_markup=get_contact_keyboard(lang)
    )
    
    await state.set_state(RegistrationStates.waiting_for_contact)

@router.message(RegistrationStates.waiting_for_contact, F.contact)
async def contact_received(message: Message, state: FSMContext):
    """Handle contact sharing"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    await message.answer(
        get_text('enter_address', lang),
        reply_markup=get_back_keyboard(lang)
    )
    
    await state.set_state(RegistrationStates.waiting_for_address)

@router.message(RegistrationStates.waiting_for_address, F.text)
async def address_received(message: Message, state: FSMContext):
    """Handle address input"""
    data = await state.get_data()
    lang = data.get('language', 'uz')
    phone = data.get('phone')
    referral_code = data.get('referral_code')
    
    address = message.text
    
    # Create user in database
    user_referral_code = await db.create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=lang,
        referred_by=referral_code
    )
    
    # Update profile with phone and address
    await db.update_user_profile(message.from_user.id, phone, address)
    
    await message.answer(
        get_text('registration_complete', lang).format(user_referral_code),
        reply_markup=get_main_menu_keyboard(lang),
        parse_mode='Markdown'
    )
    
    await state.clear()

@router.message(F.text.in_(['🌐 Тил', '🌐 Язык']))
async def change_language(message: Message):
    """Handle language change"""
    await message.answer(
        get_text('welcome'),
        reply_markup=get_language_keyboard()
    )

@router.callback_query(F.data.startswith("lang_"))
async def update_language(callback: CallbackQuery):
    """Update user language"""
    lang = callback.data.split("_")[1]
    
    # Update user language in database
    async with db.get_connection() as conn:
        await conn.execute(
            'UPDATE users SET language_code = ? WHERE telegram_id = ?',
            (lang, callback.from_user.id)
        )
        await conn.commit()
    
    await callback.message.edit_text(
        get_text('main_menu', lang),
        reply_markup=None
    )
    
    await callback.message.answer(
        get_text('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )