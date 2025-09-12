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
        "• /crear_contenido_ppv - Crear contenido pago por ver\n\n"
        "💎 <b>Pagos seguros con Telegram Stars</b> ⭐️"
    )

@router.message(Command("bot_info"))
async def bot_info_command(message: Message, bot: Bot):
    """Comando temporal para verificar información del bot"""
    try:
        # Obtener información del bot
        bot_info = await bot.get_me()
        
        # Verificar versión de aiogram
        import aiogram
        
        info_text = (
            f"🤖 <b>Información del Bot</b>\n\n"
            f"👤 <b>Nombre:</b> {bot_info.first_name}\n"
            f"🆔 <b>ID:</b> {bot_info.id}\n"
            f"📛 <b>Username:</b> @{bot_info.username}\n"
            f"🤖 <b>Es Bot:</b> {bot_info.is_bot}\n"
            f"👥 <b>Puede unirse a grupos:</b> {bot_info.can_join_groups}\n"
            f"📚 <b>Lee todos los mensajes:</b> {bot_info.can_read_all_group_messages}\n"
            f"🔍 <b>Soporta consultas inline:</b> {bot_info.supports_inline_queries}\n\n"
            f"📦 <b>Versión de aiogram:</b> {aiogram.__version__}\n\n"
            f"🔧 Verificando funciones de pago..."
        )
        
        await message.answer(info_text)
        
        # Intentar verificar si sendPaidMedia está disponible
        try:
            # Test si la función existe en el bot
            if hasattr(bot, 'send_paid_media'):
                await message.answer("✅ <b>sendPaidMedia:</b> Disponible (Bot API 8.0+)")
            else:
                await message.answer("❌ <b>sendPaidMedia:</b> No disponible (necesitas Bot API 8.0+)")
                
            # Probar también el método request directo
            try:
                await bot.request("getMe")  # Test básico
                await message.answer("✅ <b>bot.request():</b> Funcionando")
            except Exception as e:
                await message.answer(f"❌ <b>bot.request():</b> Error - {str(e)}")
                
        except Exception as e:
            await message.answer(f"❓ <b>Verificación de pagos:</b> Error - {str(e)}")
            
    except Exception as e:
        await message.answer(f"❌ Error obteniendo información del bot: {str(e)}")

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
        "• /crear_contenido_ppv - Crear contenido PPV\n\n"
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
