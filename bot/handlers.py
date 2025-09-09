# bot/handlers.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import init_db
from payments import router as payments_router
from creator_handlers import router as creator_router
from admin_handlers import router as admin_router
from ppv_handlers import router as ppv_router

router = Router()

# Include all handlers
router.include_router(payments_router)
router.include_router(creator_router)
router.include_router(admin_router)
router.include_router(ppv_router)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🌟 **¡Bienvenido a OnlyStars!** ⭐️\n\n"
        "La primera plataforma de contenido exclusivo usando Telegram Stars\n\n"
        "👥 **Para Fans:**\n"
        "• /explorar_creadores - Ver creadores disponibles\n"
        "• /suscribirme_a <ID> - Suscribirse a un creador\n"
        "• /enviar_propina <ID> <monto> - Enviar propina\n"
        "• /comprar_ppv <ID> - Comprar contenido PPV\n\n"
        "🎨 **Para Creadores:**\n"
        "• /convertirme_en_creador - Registrarse como creador\n"
        "• /mi_perfil - Ver mi perfil y estadísticas\n"
        "• /balance - Ver balance y retirar ganancias\n"
        "• /crear_contenido_ppv - Crear contenido pago por ver\n\n"
        "💎 **Pagos seguros con Telegram Stars** ⭐️"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🤖 **COMANDOS DISPONIBLES**\n\n"
        "👥 **Para todos:**\n"
        "• /start - Mensaje de bienvenida\n"
        "• /help - Esta ayuda\n\n"
        "🎨 **Para creadores:**\n"
        "• /convertirme_en_creador - Registrarse\n"
        "• /mi_perfil - Ver perfil\n"
        "• /balance - Ver saldo\n"
        "• /retirar <monto> - Retirar ganancias\n"
        "• /crear_contenido_ppv - Crear contenido PPV\n\n"
        "👥 **Para fans:**\n"
        "• /explorar_creadores - Ver creadores\n"
        "• /suscribirme_a <ID> - Suscribirse\n"
        "• /comprar_ppv <ID> - Comprar contenido\n"
        "• /enviar_propina <ID> <monto> - Enviar propina\n\n"
        "⚡️ **Powered by Telegram Stars** ⭐️"
    )

# Inicializar base de datos al cargar
init_db()
