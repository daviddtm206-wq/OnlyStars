# bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router

from dotenv import load_dotenv
import os

load_dotenv()

async def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Validate BOT_TOKEN is present
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logging.error("❌ BOT_TOKEN environment variable is required but not set!")
        logging.error("Please set BOT_TOKEN in your environment or Replit Secrets.")
        exit(1)
    
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Use memory storage for FSM
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    print(f"🤖 Bot iniciado: @{(await bot.get_me()).username}")
    print("📊 Base de datos inicializada")
    print("💫 Esperando mensajes...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
