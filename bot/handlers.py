# bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import init_db
from payments import router as payments_router

router = Router()

# Include payment handling
router.include_router(payments_router)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🌟 ¡Bienvenido a tu plataforma OnlyFans en Telegram!\n\n"
        "¿Eres creador? Usa /convertirme_en_creador\n"
        "¿Eres fan? Usa /explorar_creadores"
    )

# Inicializar base de datos al cargar
init_db()
