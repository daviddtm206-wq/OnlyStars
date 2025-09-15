"""
Handlers para el sistema de navegación jerárquica
Maneja transiciones entre menús y funciones de navegación
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database import get_creator_by_id, is_user_banned
from nav_states import MenuState, NavigationManager
from keyboards import get_main_menu, get_creator_menu, get_explore_menu, get_admin_menu, is_admin_user

router = Router()

async def show_menu(state: MenuState, message: Message, context: FSMContext):
    """Mostrar el menú correspondiente al estado actual"""
    username = message.from_user.username
    
    if state == MenuState.MAIN:
        text = "🌟 <b>ONLYSTARS - MENÚ PRINCIPAL</b>\n\n¿Qué te gustaría hacer hoy?"
        keyboard = get_main_menu(username)
        
    elif state == MenuState.CREATOR:
        creator = get_creator_by_id(message.from_user.id)
        if not creator:
            await message.answer("❌ Primero debes registrarte como creador.")
            await NavigationManager.reset_to_main(context)
            await show_menu(MenuState.MAIN, message, context)
            return
        
        text = f"🎨 <b>PANEL DE CREADOR</b>\n\n¡Hola {creator[3]}! ¿Qué deseas hacer?"
        keyboard = get_creator_menu()
        
    elif state == MenuState.EXPLORE:
        text = "🔍 <b>EXPLORAR CREADORES</b>\n\nDescubre contenido exclusivo y conecta con tus creadores favoritos"
        keyboard = get_explore_menu()
        
    elif state == MenuState.ADMIN:
        if not is_admin_user(username):
            await message.answer("❌ No tienes permisos de administrador.")
            await NavigationManager.reset_to_main(context)
            await show_menu(MenuState.MAIN, message, context)
            return
            
        text = "🛡️ <b>PANEL DE ADMINISTRACIÓN</b>\n\n¿Qué función administrativa necesitas?"
        keyboard = get_admin_menu()
        
    else:  # HELP o default
        text = (
            "ℹ️ <b>AYUDA - ONLYSTARS BOT</b>\n\n"
            "🎨 <b>Como Creador:</b>\n"
            "• Registra tu perfil y establece tu precio de suscripción\n"
            "• Crea contenido PPV (pago por ver)\n"
            "• Gestiona tus catálogos exclusivos\n"
            "• Retira tus ganancias\n\n"
            "🔍 <b>Como Fan:</b>\n"
            "• Explora creadores disponibles\n"
            "• Suscríbete y accede a contenido exclusivo\n"
            "• Compra contenido PPV individual\n"
            "• Envía propinas a tus creadores favoritos\n\n"
            "💰 <b>Pagos:</b>\n"
            "Todos los pagos se procesan con Telegram Stars ⭐️\n\n"
            "🆘 <b>¿Necesitas más ayuda?</b>\n"
            "Contacta con el soporte del bot"
        )
        keyboard = get_main_menu(username)
    
    await message.answer(text, reply_markup=keyboard)

# ==================== HANDLERS DEL MENÚ PRINCIPAL ====================

@router.message(F.text == "🎨 Ser Creador")
async def handle_ser_creador(message: Message, state: FSMContext):
    """Manejar selección de 'Ser Creador'"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes usar el bot.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    
    if creator:
        # Ya es creador, mostrar menú de creador
        await NavigationManager.push_state(MenuState.CREATOR, state)
        await show_menu(MenuState.CREATOR, message, state)
    else:
        # No es creador, mostrar opciones para convertirse
        text = (
            "🎨 <b>¡CONVIÉRTETE EN CREADOR!</b>\n\n"
            "Como creador podrás:\n"
            "• 📸 Subir contenido exclusivo PPV\n"
            "• 💰 Establecer suscripciones mensuales\n"
            "• 📊 Gestionar tus catálogos\n"
            "• 💎 Ganar dinero con tus fans\n\n"
            "💫 La comisión de la plataforma es del 20%\n"
            "⭐️ Los pagos se procesan en Telegram Stars\n\n"
            "🚀 <b>¿Estás listo para empezar?</b>\n"
            "Usa /convertirme_en_creador para registrarte"
        )
        await message.answer(text)

@router.message(F.text == "🔍 Explorar Creadores")
async def handle_explorar_creadores(message: Message, state: FSMContext):
    """Manejar selección de 'Explorar Creadores'"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes usar el bot.")
        return
    
    await NavigationManager.push_state(MenuState.EXPLORE, state)
    await show_menu(MenuState.EXPLORE, message, state)

@router.message(F.text == "ℹ️ Ayuda")
async def handle_ayuda(message: Message, state: FSMContext):
    """Manejar selección de 'Ayuda'"""
    await show_menu(MenuState.HELP, message, state)

@router.message(F.text == "🛡️ Admin Panel")
async def handle_admin_panel(message: Message, state: FSMContext):
    """Manejar selección de 'Admin Panel'"""
    username = message.from_user.username
    
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    await NavigationManager.push_state(MenuState.ADMIN, state)
    await show_menu(MenuState.ADMIN, message, state)

# ==================== HANDLERS DEL MENÚ ADMIN ====================

@router.message(F.text == "📊 Estadísticas")
async def handle_admin_stats(message: Message, state: FSMContext):
    """Manejar selección de 'Estadísticas' del admin panel"""
    username = message.from_user.username
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    from admin_handlers import admin_panel
    await admin_panel(message)

@router.message(F.text == "👥 Usuarios")
async def handle_admin_users(message: Message, state: FSMContext):
    """Manejar selección de 'Usuarios' del admin panel"""
    username = message.from_user.username
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    await message.answer(
        "👥 <b>GESTIÓN DE USUARIOS</b>\n\n"
        "📋 <b>Comandos disponibles:</b>\n"
        "• <code>/banear_usuario &lt;user_id&gt;</code> - Banear usuario\n"
        "• <code>/desbanear_usuario &lt;user_id&gt;</code> - Desbanear usuario\n"
        "• <code>/ver_usuario &lt;user_id&gt;</code> - Ver información del usuario\n\n"
        "💡 <b>Para encontrar user_id:</b>\n"
        "Pide al usuario que te envíe cualquier mensaje y verás su ID en los logs del bot."
    )

@router.message(F.text == "💰 Comisiones")
async def handle_admin_commissions(message: Message, state: FSMContext):
    """Manejar selección de 'Comisiones' del admin panel"""
    username = message.from_user.username
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    await message.answer(
        "💰 <b>GESTIÓN DE COMISIONES</b>\n\n"
        "📊 <b>Configuración actual:</b>\n"
        "• Comisión de plataforma: 20%\n"
        "• Moneda: Telegram Stars (XTR)\n"
        "• Tasa de cambio: $0.013 por estrella\n"
        "• Retiro mínimo: 1000 ⭐️\n\n"
        "💡 Para cambiar la configuración de comisiones, edita las variables de entorno en el código."
    )

@router.message(F.text == "🚫 Baneos")
async def handle_admin_bans(message: Message, state: FSMContext):
    """Manejar selección de 'Baneos' del admin panel"""
    username = message.from_user.username
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    await message.answer(
        "🚫 <b>GESTIÓN DE BANEOS</b>\n\n"
        "📋 <b>Comandos de moderación:</b>\n"
        "• <code>/banear_usuario &lt;user_id&gt;</code> - Banear usuario\n"
        "• <code>/desbanear_usuario &lt;user_id&gt;</code> - Desbanear usuario\n"
        "• <code>/lista_baneados</code> - Ver usuarios baneados\n\n"
        "⚠️ <b>Los usuarios baneados:</b>\n"
        "• No pueden usar el bot\n"
        "• No pueden realizar transacciones\n"
        "• No pueden acceder a contenido"
    )

@router.message(F.text == "📢 Anuncio Global")
async def handle_admin_broadcast(message: Message, state: FSMContext):
    """Manejar selección de 'Anuncio Global' del admin panel"""
    username = message.from_user.username
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    await message.answer(
        "📢 <b>ANUNCIO GLOBAL</b>\n\n"
        "🔊 Para enviar un mensaje a todos los usuarios del bot:\n\n"
        "📝 <b>Formato:</b>\n"
        "<code>/anuncio_global &lt;mensaje&gt;</code>\n\n"
        "📌 <b>Ejemplo:</b>\n"
        "<code>/anuncio_global ¡Nueva función disponible! Ahora puedes crear catálogos personalizados.</code>\n\n"
        "⚠️ <b>Importante:</b>\n"
        "• El mensaje se enviará a TODOS los usuarios registrados\n"
        "• Úsalo con moderación para evitar spam"
    )

@router.message(F.text == "🔧 Configuración")
async def handle_admin_config(message: Message, state: FSMContext):
    """Manejar selección de 'Configuración' del admin panel"""
    username = message.from_user.username
    if not is_admin_user(username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    await message.answer(
        "🔧 <b>CONFIGURACIÓN DEL SISTEMA</b>\n\n"
        "⚙️ <b>Variables actuales:</b>\n"
        "• Comisión: 20%\n"
        "• Moneda: XTR (Telegram Stars)\n"
        "• Retiro mínimo: 1000 ⭐️\n"
        "• Modo de retiro: REAL\n\n"
        "📋 <b>Comandos de configuración:</b>\n"
        "• <code>/config_comision &lt;porcentaje&gt;</code>\n"
        "• <code>/config_retiro_min &lt;cantidad&gt;</code>\n"
        "• <code>/reiniciar_base_datos</code> (¡CUIDADO!)\n\n"
        "⚠️ <b>Los cambios requieren reiniciar el bot</b>"
    )

# ==================== HANDLER PARA VOLVER ====================

@router.message(F.text == "⬅️ Volver")
async def handle_volver(message: Message, state: FSMContext):
    """Manejar botón 'Volver' - navegar al menú anterior"""
    previous_state = await NavigationManager.pop_state(state)
    await show_menu(previous_state, message, state)