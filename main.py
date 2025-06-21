"""Main module for the Arzon Telegram delivery bot."""
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database.models import db
from handlers import start, catalog, cart, referral, admin, profile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with sample data."""
    await db.init_db()

    # Add sample categories and products
    async with db.get_connection() as conn:
        # Check if categories exist
        cursor = await conn.execute('SELECT COUNT(*) FROM categories')
        count = await cursor.fetchone()

        if count[0] == 0:
            # Add sample categories
            categories = [
                ("Овқатлар", "Еда", "Турли хил овқатлар",
                 "Различная еда", None),
                ("Ичимликлар", "Напитки", "Совуқ ва иссиқ ичимликлар",
                 "Холодные и горячие напитки", None),
                ("Десертлар", "Десерты", "Ширин таомлар",
                 "Сладкие блюда", None),
                ("Мева-сабзавот", "Фрукты-овощи", "Янги мева ва сабзавотлар",
                 "Свежие фрукты и овощи", None)
            ]

            for cat in categories:
                await conn.execute('''
                    INSERT INTO categories 
                    (name_uz, name_ru, description_uz, description_ru, image_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', cat)

            # Add sample products
            products = [
                # Food category (id=1)
                (1, "Плов", "Плов", "Анъанавий ўзбек плови",
                 "Традиционный узбекский плов", 25000, None),
                (1, "Лагман", "Лагман", "Қўй гўшти билан лагман",
                 "Лагман с бараниной", 22000, None),
                (1, "Шашлик", "Шашлык", "Қўй гўшти шашлиги",
                 "Шашлык из баранины", 35000, None),
                (1, "Манты", "Манты", "Буғда пишган манты",
                 "Манты на пару", 18000, None),

                # Drinks category (id=2)
                (2, "Чой", "Чай", "Кўк чой", "Зеленый чай", 3000, None),
                (2, "Кофе", "Кофе", "Эспрессо кофе", "Кофе эспрессо", 8000, None),
                (2, "Кола", "Кола", "Совуқ кола", "Холодная кола", 5000, None),
                (2, "Сув", "Вода", "Тоза ичимлик суви",
                 "Чистая питьевая вода", 2000, None),

                # Desserts category (id=3)
                (3, "Торт", "Торт", "Шоколадли торт",
                 "Шоколадный торт", 45000, None),
                (3, "Мороженое", "Мороженое", "Ванилли мороженое",
                 "Ванильное мороженое", 8000, None),

                # Fruits-vegetables category (id=4)
                (4, "Олма", "Яблоки", "Янги олма", "Свежие яблоки", 12000, None),
                (4, "Банан", "Бананы", "Ширин банан",
                 "Сладкие бананы", 15000, None),
                (4, "Помидор", "Помидоры", "Янги помидор",
                 "Свежие помидоры", 8000, None),
                (4, "Картошка", "Картофель", "Картошка",
                 "Картофель", 6000, None)
            ]

            for prod in products:
                await conn.execute('''
                    INSERT INTO products 
                    (category_id, name_uz, name_ru, description_uz, 
                     description_ru, price, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', prod)

            await conn.commit()
            logger.info("Sample data added to database")


async def on_startup():
    """Actions on bot startup."""
    logger.info("Initializing database...")
    await init_database()
    logger.info("Database initialized successfully!")


async def on_shutdown():
    """Actions on bot shutdown."""
    logger.info("Bot is shutting down...")


async def main():
    """Main function to run the bot."""
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return

    # Initialize bot and dispatcher
    bot = Bot(token=Config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Set startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register routers
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(referral.router)
    dp.include_router(admin.router)
    dp.include_router(profile.router)

    logger.info("Bot started successfully!")

    try:
        # Start polling
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as error:
        logger.error("Unexpected error: %s", error)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())