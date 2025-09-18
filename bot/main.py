# bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from database import init_db
from videocall_system import videocall_manager

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

    # Initialize database
    try:
        init_db()
        logging.info("✅ Database initialized successfully")
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")
        exit(1)
    
    # Get bot info first
    try:
        bot_info = await bot.get_me()
    except Exception as e:
        logging.error(f"❌ Failed to get bot info: {e}")
        exit(1)
    
    # Initialize videocall manager
    try:
        success = await videocall_manager.initialize(bot_info.id)
        if success:
            logging.info("✅ VideoCall system initialized successfully")
            print("🎥 Sistema de videollamadas inicializado")
        else:
            logging.warning("⚠️ VideoCall system initialization failed")
            print("⚠️ Sistema de videollamadas no disponible (verifica credenciales)")
    except Exception as e:
        logging.error(f"❌ VideoCall system initialization error: {e}")
        print("⚠️ Sistema de videollamadas no disponible")
    
    print(f"🤖 Bot iniciado: @{bot_info.username}")
    print("📊 Base de datos inicializada")
    print("💫 Esperando mensajes...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
