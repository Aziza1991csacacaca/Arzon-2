from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from localization.texts import get_text
from typing import List, Dict

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
    )
    return builder.as_markup()

def get_contact_keyboard(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Contact sharing keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=get_text('send_contact', lang), request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_location_keyboard(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Location sharing keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=get_text('send_location', lang), request_location=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_keyboard(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=get_text('btn_categories', lang)),
        KeyboardButton(text=get_text('btn_cart', lang)),
        KeyboardButton(text=get_text('btn_orders', lang)),
        KeyboardButton(text=get_text('btn_profile', lang)),
        KeyboardButton(text=get_text('btn_referral', lang)),
        KeyboardButton(text=get_text('btn_language', lang))
    )
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_categories_keyboard(categories: List[Dict], lang: str = 'uz') -> InlineKeyboardMarkup:
    """Categories inline keyboard"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        name = category[f'name_{lang}'] if f'name_{lang}' in category else category['name_uz']
        builder.add(
            InlineKeyboardButton(
                text=name,
                callback_data=f"category_{category['id']}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_menu")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_products_keyboard(products: List[Dict], lang: str = 'uz') -> InlineKeyboardMarkup:
    """Products inline keyboard"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        name = product[f'name_{lang}'] if f'name_{lang}' in product else product['name_uz']
        price = f"{product['price']:,} сўм"
        builder.add(
            InlineKeyboardButton(
                text=f"{name} - {price}",
                callback_data=f"product_{product['id']}"
            )
        )
    
    builder.add(
        InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_categories")
    )
    builder.adjust(1)
    return builder.as_markup()

def get_product_detail_keyboard(product_id: int, lang: str = 'uz') -> InlineKeyboardMarkup:
    """Product detail keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=get_text('add_to_cart', lang),
            callback_data=f"add_to_cart_{product_id}"
        ),
        InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_products")
    )
    builder.adjust(1)
    return builder.as_markup()

def get_cart_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Cart management keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=get_text('checkout', lang), callback_data="checkout"),
        InlineKeyboardButton(text=get_text('clear_cart', lang), callback_data="clear_cart"),
        InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_menu")
    )
    builder.adjust(1)
    return builder.as_markup()

def get_payment_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Payment methods keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=get_text('payment_cash', lang), callback_data="payment_cash"),
        InlineKeyboardButton(text=get_text('payment_payme', lang), callback_data="payment_payme"),
        InlineKeyboardButton(text=get_text('payment_click', lang), callback_data="payment_click"),
        InlineKeyboardButton(text=get_text('payment_uzcard', lang), callback_data="payment_uzcard")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_back_keyboard(lang: str = 'uz') -> ReplyKeyboardMarkup:
    """Simple back button keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=get_text('btn_back', lang)))
    return builder.as_markup(resize_keyboard=True)

def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin menu keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders"),
        InlineKeyboardButton(text="📦 Товары", callback_data="admin_products"),
        InlineKeyboardButton(text="📂 Категории", callback_data="admin_categories"),
        InlineKeyboardButton(text="🤖 AI Аналитика", callback_data="admin_ai_insights")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_profile_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    """Profile management keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=get_text('edit_phone', lang), callback_data="edit_phone"),
        InlineKeyboardButton(text=get_text('edit_address', lang), callback_data="edit_address"),
        InlineKeyboardButton(text=get_text('my_orders', lang), callback_data="my_orders"),
        InlineKeyboardButton(text=get_text('btn_back', lang), callback_data="back_to_menu")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_categories_management_keyboard() -> InlineKeyboardMarkup:
    """Categories management keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="➕ Добавить категорию", callback_data="add_category"),
        InlineKeyboardButton(text="📝 Редактировать", callback_data="edit_categories"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_categories"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")
    )
    builder.adjust(1)
    return builder.as_markup()

def get_products_management_keyboard() -> InlineKeyboardMarkup:
    """Products management keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product"),
        InlineKeyboardButton(text="📝 Редактировать", callback_data="edit_products"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_products"),
        InlineKeyboardButton(text="📊 Популярные", callback_data="popular_products"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_orders_management_keyboard() -> InlineKeyboardMarkup:
    """Orders management keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🆕 Новые", callback_data="new_orders"),
        InlineKeyboardButton(text="✅ Подтвержденные", callback_data="confirmed_orders"),
        InlineKeyboardButton(text="🚚 В доставке", callback_data="delivering_orders"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="orders_stats"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_admin")
    )
    builder.adjust(2)
    return builder.as_markup()