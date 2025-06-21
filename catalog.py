from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import db
from keyboards.keyboards import (
    get_categories_keyboard, get_products_keyboard, 
    get_product_detail_keyboard, get_main_menu_keyboard
)
from localization.texts import get_text

router = Router()

@router.message(F.text.in_(['📂 Категориялар', '📂 Категории']))
async def show_categories(message: Message):
    """Show product categories"""
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    lang = user.get('language_code', 'uz')
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("Категориялар топилмади")
        return
    
    await message.answer(
        get_text('choose_category', lang),
        reply_markup=get_categories_keyboard(categories, lang)
    )

@router.callback_query(F.data.startswith("category_"))
async def show_products(callback: CallbackQuery):
    """Show products in category"""
    category_id = int(callback.data.split("_")[1])
    
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    products = await db.get_products_by_category(category_id)
    
    if not products:
        await callback.answer("Бу категорияда маҳсулотлар йўқ")
        return
    
    await callback.message.edit_text(
        "📦 Маҳсулотларни танланг:",
        reply_markup=get_products_keyboard(products, lang)
    )

@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    """Show product details"""
    product_id = int(callback.data.split("_")[1])
    
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    # Get product details
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Маҳсулот топилмади")
        return
    
    name = product[f'name_{lang}'] if f'name_{lang}' in product else product['name_uz']
    description = product[f'description_{lang}'] if f'description_{lang}' in product else product['description_uz']
    
    text = get_text('product_details', lang).format(
        name, f"{product['price']:,}", description or "Тафсилот йўқ"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_product_detail_keyboard(product_id, lang),
        parse_mode='Markdown'
    )

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Add product to cart"""
    product_id = int(callback.data.split("_")[3])
    
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    await db.add_to_cart(callback.from_user.id, product_id, 1)
    
    await callback.answer(get_text('product_added_to_cart', lang))

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Go back to categories"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    categories = await db.get_categories()
    
    await callback.message.edit_text(
        get_text('choose_category', lang),
        reply_markup=get_categories_keyboard(categories, lang)
    )

@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):
    """Go back to products (need to store category_id in state)"""
    await callback.answer("Орқага қайтиш...")

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Go back to main menu"""
    user = await db.get_user(callback.from_user.id)
    lang = user.get('language_code', 'uz')
    
    await callback.message.edit_text(get_text('main_menu', lang))
    await callback.message.answer(
        get_text('main_menu', lang),
        reply_markup=get_main_menu_keyboard(lang)
    )