from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import db
from keyboards.keyboards import get_main_menu_keyboard
from localization.texts import get_text
from io import BytesIO
from aiogram.types import BufferedInputFile

# Try to import qrcode, but handle if not available
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

router = Router()

class ReferralStates(StatesGroup):
    waiting_for_code = State()

@router.message(F.text.in_(['🎁 Реферал', '🎁 Дўстларни таклиф қилиш']))
async def show_referral_info(message: Message):
    """Show referral information"""
    user = await db.get_user(message.from_user.id)
    if not user:
        return
    
    lang = user.get('language_code', 'uz')
    
    # Get referral statistics
    async with db.get_connection() as conn:
        cursor = await conn.execute('''
            SELECT COUNT(*) as referred_count 
            FROM referrals 
            WHERE referrer_id = ?
        ''', (message.from_user.id,))
        result = await cursor.fetchone()
        referred_count = result[0] if result else 0
    
    referral_code = user.get('referral_code', 'N/A')
    bonus_balance = user.get('bonus_balance', 0)
    
    # Create referral link
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"
    
    text = get_text('referral_info', lang).format(
        referral_code, referred_count, f"{bonus_balance:,}"
    )
    
    text += f"\n\n🔗 **Реферал ҳавола:**\n`{referral_link}`"
    
    if QRCODE_AVAILABLE:
        try:
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(referral_link)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            bio = BytesIO()
            qr_image.save(bio, format='PNG')
            bio.seek(0)
            
            await message.answer_photo(
                BufferedInputFile(bio.read(), filename="referral_qr.png"),
                caption=text,
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(lang)
            )
        except Exception as e:
            # Fallback to text only
            await message.answer(
                text,
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(lang)
            )
    else:
        # Send text only if QR code library not available
        await message.answer(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(lang)
        )

async def check_referral_bonus(referrer_id: int):
    """Check and award referral bonus if conditions are met"""
    async with db.get_connection() as conn:
        # Count active referrals
        cursor = await conn.execute('''
            SELECT COUNT(*) as count 
            FROM referrals r
            JOIN users u ON r.referred_id = u.telegram_id
            WHERE r.referrer_id = ? AND u.is_active = 1
        ''', (referrer_id,))
        result = await cursor.fetchone()
        active_referrals = result[0] if result else 0
        
        # Award bonus if reached threshold
        if active_referrals >= 5:  # REFERRAL_REQUIRED_FRIENDS from config
            # Check if bonus already awarded
            cursor = await conn.execute('''
                SELECT bonus_awarded FROM referrals 
                WHERE referrer_id = ? AND bonus_awarded = 1
                LIMIT 1
            ''', (referrer_id,))
            
            if not await cursor.fetchone():
                # Award bonus
                await conn.execute('''
                    UPDATE users 
                    SET bonus_balance = bonus_balance + ? 
                    WHERE telegram_id = ?
                ''', (5000, referrer_id))  # REFERRAL_BONUS_AMOUNT
                
                # Mark as awarded
                await conn.execute('''
                    UPDATE referrals 
                    SET bonus_awarded = 1 
                    WHERE referrer_id = ?
                ''', (referrer_id,))
                
                await conn.commit()
                return True
    
    return False