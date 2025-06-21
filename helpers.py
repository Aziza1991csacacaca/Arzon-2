import re
from typing import Optional
from datetime import datetime, timedelta

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    phone_digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Uzbek phone number
    # Uzbek numbers: +998XXXXXXXXX (13 digits total)
    if len(phone_digits) == 13 and phone_digits.startswith('998'):
        return True
    elif len(phone_digits) == 12 and phone_digits.startswith('98'):
        return True
    elif len(phone_digits) == 9:
        return True
    
    return False

def format_phone(phone: str) -> str:
    """Format phone number to standard format"""
    phone_digits = re.sub(r'\D', '', phone)
    
    if len(phone_digits) == 9:
        return f"+998{phone_digits}"
    elif len(phone_digits) == 12 and phone_digits.startswith('98'):
        return f"+{phone_digits}"
    elif len(phone_digits) == 13 and phone_digits.startswith('998'):
        return f"+{phone_digits}"
    
    return phone

def format_price(price: int) -> str:
    """Format price with thousand separators"""
    return f"{price:,}".replace(',', ' ')

def calculate_delivery_time() -> str:
    """Calculate estimated delivery time"""
    now = datetime.now()
    delivery_time = now + timedelta(minutes=30)
    return delivery_time.strftime("%H:%M")

def generate_order_number() -> str:
    """Generate unique order number"""
    now = datetime.now()
    return f"ORD{now.strftime('%Y%m%d%H%M%S')}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def is_valid_coordinates(lat: float, lon: float) -> bool:
    """Validate GPS coordinates"""
    # Uzbekistan approximate coordinates
    # Latitude: 37.0 to 45.6
    # Longitude: 55.9 to 73.2
    if 37.0 <= lat <= 45.6 and 55.9 <= lon <= 73.2:
        return True
    return False

def get_order_status_emoji(status: str) -> str:
    """Get emoji for order status"""
    status_emojis = {
        'new': '🆕',
        'confirmed': '✅',
        'preparing': '👨‍🍳',
        'ready': '📦',
        'delivering': '🚚',
        'completed': '✅',
        'cancelled': '❌'
    }
    return status_emojis.get(status, '❓')

def get_payment_method_emoji(method: str) -> str:
    """Get emoji for payment method"""
    method_emojis = {
        'cash': '💵',
        'payme': '💳',
        'click': '💳',
        'uzcard': '💳',
        'card': '💳'
    }
    return method_emojis.get(method, '💰')

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text