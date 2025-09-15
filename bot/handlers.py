# bot/handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from database import init_db
from payments import router as payments_router
from creator_handlers import router as creator_router
from admin_handlers import router as admin_router
from ppv_handlers import router as ppv_router
from catalog_handlers import router as catalog_router

router = Router()

# Include all handlers
router.include_router(payments_router)
router.include_router(creator_router)
router.include_router(admin_router)
router.include_router(ppv_router)
router.include_router(catalog_router)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🌟 <b>¡Bienvenido a OnlyStars!</b> ⭐️\n\n"
        "La primera plataforma de contenido exclusivo usando Telegram Stars\n\n"
        "👥 <b>Para Fans:</b>\n"
        "• /explorar_creadores - Ver creadores disponibles\n"
        "• /suscribirme_a &lt;ID&gt; - Suscribirse a un creador\n"
        "• /mis_catalogos - Ver catálogos de tus suscripciones\n"
        "• /enviar_propina &lt;ID&gt; &lt;monto&gt; - Enviar propina\n"
        "• /comprar_ppv &lt;ID&gt; - Comprar contenido PPV\n\n"
        "🎨 <b>Para Creadores:</b>\n"
        "• /convertirme_en_creador - Registrarse como creador\n"
        "• /mi_perfil - Ver mi perfil y estadísticas\n"
        "• /balance - Ver balance y retirar ganancias\n"
        "• /crear_contenido_ppv - Crear contenido pago por ver\n"
        "• /mi_catalogo - Gestionar mi catálogo\n\n"
        "💎 <b>Pagos seguros con Telegram Stars</b> ⭐️"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🤖 <b>COMANDOS DISPONIBLES</b>\n\n"
        "👥 <b>Para todos:</b>\n"
        "• /start - Mensaje de bienvenida\n"
        "• /help - Esta ayuda\n\n"
        "🎨 <b>Para creadores:</b>\n"
        "• /convertirme_en_creador - Registrarse\n"
        "• /mi_perfil - Ver perfil\n"
        "• /balance - Ver saldo\n"
        "• /retirar &lt;monto&gt; - Retirar ganancias\n"
        "• /crear_contenido_ppv - Crear contenido PPV\n"
        "• /mi_catalogo - Gestionar mi catálogo\n\n"
        "👥 <b>Para fans:</b>\n"
        "• /explorar_creadores - Ver creadores\n"
        "• /suscribirme_a &lt;ID&gt; - Suscribirse\n"
        "• /mis_catalogos - Ver catálogos exclusivos\n"
        "• /comprar_ppv &lt;ID&gt; - Comprar contenido\n"
        "• /enviar_propina &lt;ID&gt; &lt;monto&gt; - Enviar propina\n\n"
        "⚡️ <b>Powered by Telegram Stars</b> ⭐️"
    )

# Inicializar base de datos al cargar
init_db()

