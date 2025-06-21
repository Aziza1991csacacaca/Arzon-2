"""Configuration module for the Arzon Telegram bot."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class containing all bot settings."""
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ADMIN_IDS = (
        list(map(int, os.getenv('ADMIN_IDS', '').split(',')))
        if os.getenv('ADMIN_IDS') else []
    )
    PAYME_MERCHANT_ID = os.getenv('PAYME_MERCHANT_ID')
    CLICK_MERCHANT_ID = os.getenv('CLICK_MERCHANT_ID')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///arzon_bot.db')

    # Languages
    SUPPORTED_LANGUAGES = ['uz', 'ru']
    DEFAULT_LANGUAGE = 'uz'

    # Referral settings
    REFERRAL_BONUS_AMOUNT = 5000  # in som
    REFERRAL_REQUIRED_FRIENDS = 5

    # AI settings
    AI_ENABLED = bool(os.getenv('OPENAI_API_KEY'))