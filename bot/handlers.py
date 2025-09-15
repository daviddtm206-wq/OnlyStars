# bot/handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import init_db, get_creator_by_id, is_user_banned
from keyboards import get_main_keyboard, get_fan_keyboard
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
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes usar el bot.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    keyboard = get_main_keyboard(message.from_user.id)
    
    if creator:
        welcome_text = (
            f"🌟 <b>¡Bienvenido de vuelta, {creator[3]}!</b> ⭐️\n\n"
            f"🎨 <b>Panel de Creador Activo</b>\n"
            f"Usa los botones de abajo para gestionar tu cuenta.\n\n"
            f"💎 <b>Pagos seguros con Telegram Stars</b> ⭐️"
        )
    else:
        welcome_text = (
            "🌟 <b>¡Bienvenido a OnlyStars!</b> ⭐️\n\n"
            "La primera plataforma de contenido exclusivo usando Telegram Stars\n\n"
            "👥 <b>Explora creadores</b> y accede a contenido exclusivo\n"
            "🎨 <b>Conviértete en creador</b> y monetiza tu contenido\n\n"
            "💎 <b>Pagos seguros con Telegram Stars</b> ⭐️"
        )
    
    await message.answer(welcome_text, reply_markup=keyboard)

# HANDLERS PARA BOTONES DEL TECLADO

@router.message(F.text == "🔍 Explorar Creadores")
async def keyboard_explore_creators(message: Message):
    from creator_handlers import explore_creators
    await explore_creators(message)

@router.message(F.text == "📺 Mis Catálogos")
async def keyboard_my_catalogs(message: Message, state: FSMContext):
    from catalog_handlers import show_my_catalogs
    await show_my_catalogs(message, state)

@router.message(F.text == "🎨 Ser Creador")
async def keyboard_become_creator(message: Message, state: FSMContext):
    from creator_handlers import start_creator_registration
    await start_creator_registration(message, state)

@router.message(F.text == "💰 Enviar Propina")
async def keyboard_send_tip(message: Message):
    await message.answer(
        "💰 <b>ENVIAR PROPINA</b>\n\n"
        "Para enviar una propina a un creador, usa:\n"
        "<code>/enviar_propina &lt;ID_creador&gt; &lt;monto&gt;</code>\n\n"
        "📌 <b>Ejemplo:</b>\n"
        "<code>/enviar_propina 123456789 100</code>\n"
        "(Envía 100 ⭐️ al creador con ID 123456789)\n\n"
        "💡 Puedes encontrar el ID de los creadores en 🔍 Explorar Creadores"
    )

@router.message(F.text == "🛒 Comprar PPV")
async def keyboard_buy_ppv(message: Message):
    await message.answer(
        "🛒 <b>COMPRAR CONTENIDO PPV</b>\n\n"
        "Para comprar contenido PPV de un creador, usa:\n"
        "<code>/comprar_ppv &lt;ID_contenido&gt;</code>\n\n"
        "📌 <b>Ejemplo:</b>\n"
        "<code>/comprar_ppv 42</code>\n\n"
        "💡 <b>¿Dónde encuentro contenido PPV?</b>\n"
        "• En 📺 Mis Catálogos (si estás suscrito)\n"
        "• En perfiles de creadores públicos\n"
        "• En anuncios de creadores"
    )

@router.message(F.text == "👤 Mi Perfil")
async def keyboard_my_profile(message: Message):
    from creator_handlers import my_profile
    await my_profile(message)

@router.message(F.text == "💎 Balance")
async def keyboard_balance(message: Message):
    from creator_handlers import check_balance
    await check_balance(message)

@router.message(F.text == "📸 Crear PPV")
async def keyboard_create_ppv(message: Message, state: FSMContext):
    from creator_handlers import create_ppv_content
    await create_ppv_content(message, state)

@router.message(F.text == "📊 Mi Catálogo")
async def keyboard_my_catalog(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer(
            "❌ <b>No eres un creador registrado</b>\n\n"
            "Para gestionar un catálogo, primero debes registrarte como creador.\n"
            "Usa el botón 🎨 Ser Creador para comenzar."
        )
        return
    
    # Importar y ejecutar función de gestión de catálogo
    from admin_handlers import my_catalog_management
    await my_catalog_management(message)

@router.message(F.text == "⚙️ Editar Perfil")
async def keyboard_edit_profile(message: Message):
    from creator_handlers import edit_profile_menu
    await edit_profile_menu(message)

@router.message(F.text == "🔍 Explorar")
async def keyboard_explore_as_creator(message: Message):
    from creator_handlers import explore_creators
    await explore_creators(message)

@router.message(F.text == "👥 Ver Como Fan")
async def keyboard_view_as_fan(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
        
    keyboard = get_fan_keyboard()
    await message.answer(
        "👥 <b>VISTA DE FAN ACTIVADA</b>\n\n"
        "Ahora ves OnlyStars desde la perspectiva de un fan.\n"
        "Puedes explorar creadores y acceder a contenido exclusivo.\n\n"
        "💡 Usa '🎨 Volver a Creador' para regresar a tu panel de creador.",
        reply_markup=keyboard
    )

@router.message(F.text == "🎨 Volver a Creador")
async def keyboard_back_to_creator(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
        
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
        
    keyboard = get_main_keyboard(message.from_user.id)
    await message.answer(
        f"🎨 <b>PANEL DE CREADOR RESTAURADO</b>\n\n"
        f"Bienvenido de vuelta, {creator[3]}!\n"
        f"Tu panel de creador está activo nuevamente.",
        reply_markup=keyboard
    )

@router.message(F.text == "🛡️ Admin Panel")
async def keyboard_admin_panel(message: Message):
    from admin_handlers import admin_panel
    await admin_panel(message)

@router.message(F.text == "ℹ️ Ayuda")
async def keyboard_help(message: Message):
    creator = get_creator_by_id(message.from_user.id)
    
    if creator:
        help_text = (
            "🤖 <b>AYUDA - PANEL DE CREADOR</b>\n\n"
            "🎨 <b>Gestión de Contenido:</b>\n"
            "• 📸 Crear PPV - Sube fotos/videos de pago\n"
            "• 📊 Mi Catálogo - Gestiona tu contenido\n"
            "• ⚙️ Editar Perfil - Cambia tu información\n\n"
            "💰 <b>Finanzas:</b>\n"
            "• 💎 Balance - Ver y retirar ganancias\n"
            "• Comisión de plataforma: 20%\n"
            "• Retiro mínimo: 1000 ⭐️\n\n"
            "👥 <b>Interacción:</b>\n"
            "• 🔍 Explorar - Ve otros creadores\n"
            "• 👥 Ver Como Fan - Cambia de perspectiva\n\n"
            "⚡️ <b>Powered by Telegram Stars</b> ⭐️"
        )
    else:
        help_text = (
            "🤖 <b>AYUDA - PANEL DE FAN</b>\n\n"
            "🔍 <b>Descubrimiento:</b>\n"
            "• Explorar Creadores - Ve perfiles y precios\n"
            "• Catálogos - Contenido de tus suscripciones\n\n"
            "💰 <b>Pagos:</b>\n"
            "• Enviar Propina - Apoya a tus creadores favoritos\n"
            "• Comprar PPV - Accede a contenido exclusivo\n"
            "• Suscripciones - Acceso mensual ilimitado\n\n"
            "🎨 <b>¿Quieres ganar dinero?</b>\n"
            "• Ser Creador - Registra tu cuenta\n"
            "• Monetiza fotos, videos y contenido exclusivo\n\n"
            "⚡️ <b>Powered by Telegram Stars</b> ⭐️"
        )
    
    await message.answer(help_text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await keyboard_help(message)

# Inicializar base de datos al cargar
init_db()

