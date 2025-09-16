# bot/handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import init_db, get_creator_by_id, is_user_banned
from keyboards import get_main_keyboard, get_fan_keyboard, get_main_menu
from nav_states import MenuState, NavigationManager
from payments import router as payments_router
from creator_handlers import router as creator_router
from admin_handlers import router as admin_router
from ppv_handlers import router as ppv_router
from catalog_handlers import router as catalog_router
from nav_handlers import router as nav_router

router = Router()

# Include all handlers
router.include_router(nav_router)  # Sistema de navegación jerárquica
router.include_router(payments_router)
router.include_router(creator_router)
router.include_router(admin_router)
router.include_router(ppv_router)
router.include_router(catalog_router)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes usar el bot.")
        return
    
    # LIMPIAR COMPLETAMENTE el estado FSM para evitar conflictos
    await state.clear()
    
    # Resetear navegación al menú principal
    await NavigationManager.reset_to_main(state)
    
    creator = get_creator_by_id(message.from_user.id)
    username = message.from_user.username
    keyboard = get_main_menu(username)
    
    if creator:
        welcome_text = (
            f"🌟 <b>¡Bienvenido de vuelta, {creator[3]}!</b> ⭐️\n\n"
            f"🎨 <b>Panel de Creador Activo</b>\n"
            f"Usa los botones de abajo para navegar por las funciones disponibles.\n\n"
            f"💎 <b>Pagos seguros con Telegram Stars</b> ⭐️"
        )
    else:
        welcome_text = (
            "🌟 <b>¡Bienvenido a OnlyStars!</b> ⭐️\n\n"
            "La primera plataforma de contenido exclusivo usando Telegram Stars\n\n"
            "👥 <b>Explora creadores</b> y accede a contenido exclusivo\n"
            "🎨 <b>Conviértete en creador</b> y monetiza tu contenido\n\n"
            "💎 <b>Pagos seguros con Telegram Stars</b> ⭐️\n\n"
            "Usa los botones del menú para navegar por las opciones disponibles."
        )
    
    # Primero remover teclado anterior, luego enviar el nuevo
    from aiogram.types import ReplyKeyboardRemove
    await message.answer("🔄 Actualizando menú...", reply_markup=ReplyKeyboardRemove())
    await message.answer(welcome_text, reply_markup=keyboard)

# HANDLERS PARA BOTONES DEL TECLADO (solo los no manejados por navegación jerárquica)

@router.message(F.text == "📺 Mis Catálogos")
async def keyboard_my_catalogs(message: Message, state: FSMContext):
    from catalog_handlers import show_my_catalogs
    await show_my_catalogs(message, state)

# NOTA: Los siguientes botones son manejados por nav_handlers.py:
# - "🎨 Ser Creador" 
# - "🔍 Explorar Creadores"
# - "🛡️ Admin Panel"
# - "ℹ️ Ayuda"
# - "⬅️ Volver"

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
    from keyboards import get_creator_profile_menu
    await my_profile(message)
    # Cambiar al submenú del perfil
    await message.answer(
        "🎛️ <b>PANEL DE CONTROL</b>\n\n"
        "Selecciona una opción del menú:",
        reply_markup=get_creator_profile_menu()
    )

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
async def keyboard_back_to_creator(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
        
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    # Resetear navegación al menú principal usando el nuevo sistema
    await NavigationManager.reset_to_main(state)
    username = message.from_user.username
    keyboard = get_main_menu(username)
    
    await message.answer(
        f"🎨 <b>PANEL DE CREADOR RESTAURADO</b>\n\n"
        f"Bienvenido de vuelta, {creator[3]}!\n"
        f"Tu panel de creador está activo nuevamente.",
        reply_markup=keyboard
    )

# ==================== HANDLERS PARA SUBMENÚ DE PERFIL ====================

@router.message(F.text == "💰 Ver Balance")
async def profile_check_balance(message: Message):
    from creator_handlers import check_balance
    await check_balance(message)

@router.message(F.text == "💸 Retirar Ganancias")
async def profile_withdraw_menu(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    await message.answer(
        "💸 <b>RETIRAR GANANCIAS</b>\n\n"
        "Para retirar tus ganancias, usa:\n"
        "<code>/retirar &lt;monto&gt;</code>\n\n"
        "📌 <b>Ejemplo:</b>\n"
        "<code>/retirar 1000</code>\n\n"
        "💡 Verifica tu balance primero con '💰 Ver Balance'"
    )

@router.message(F.text == "🎥 Crear Contenido PPV")
async def profile_create_ppv(message: Message, state: FSMContext):
    from creator_handlers import create_ppv_content
    await create_ppv_content(message, state)

@router.message(F.text == "✏️ Editar Perfil")
async def profile_edit_profile(message: Message):
    from creator_handlers import edit_profile_menu
    await edit_profile_menu(message)

@router.message(F.text == "📈 Mis Estadísticas")
async def profile_my_stats(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    await message.answer(
        "📈 <b>MIS ESTADÍSTICAS</b>\n\n"
        "Esta función estará disponible pronto.\n"
        "Podrás ver estadísticas detalladas de:\n"
        "• Ingresos por mes\n"
        "• Crecimiento de suscriptores\n"
        "• Contenido más popular\n"
        "• Y mucho más..."
    )

@router.message(F.text == "🔙 Volver al Menú")
async def profile_back_to_main(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    # Resetear navegación al menú principal
    await NavigationManager.reset_to_main(state)
    username = message.from_user.username
    keyboard = get_main_menu(username)
    
    await message.answer(
        f"🎨 <b>MENÚ PRINCIPAL</b>\n\n"
        f"Bienvenido de vuelta, {creator[3]}!\n"
        f"Usa los botones para navegar por las opciones.",
        reply_markup=keyboard
    )

# Los siguientes handlers han sido movidos a nav_handlers.py para evitar conflictos:
# - keyboard_admin_panel: "🛡️ Admin Panel" 
# - keyboard_help: "ℹ️ Ayuda"

@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    from nav_handlers import show_menu
    from nav_states import MenuState
    await show_menu(MenuState.HELP, message, state)

# Inicializar base de datos al cargar
init_db()

