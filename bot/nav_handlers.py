"""
Handlers para el sistema de navegación jerárquica
Maneja transiciones entre menús y funciones de navegación
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import get_creator_by_id, is_user_banned, get_user_balance, get_ppv_by_creator
from nav_states import MenuState, NavigationManager
from keyboards import get_main_menu, get_main_keyboard, get_creator_menu, get_explore_menu, get_admin_menu, get_creator_onboarding_menu, is_admin_user, get_creator_profile_main_keyboard, get_creator_profile_submenu_keyboard

router = Router()

async def show_menu(state: MenuState, message: Message, context: FSMContext):
    """Mostrar el menú correspondiente al estado actual"""
    username = message.from_user.username
    
    if state == MenuState.MAIN:
        text = "🌟 <b>ONLYSTARS - MENÚ PRINCIPAL</b>\n\n¿Qué te gustaría hacer hoy?"
        keyboard = get_main_keyboard(message.from_user.id, username)
        
    elif state == MenuState.CREATOR:
        creator = get_creator_by_id(message.from_user.id)
        if not creator:
            # Mostrar panel de onboarding en lugar de redirigir
            text = (
                "🎨 <b>¡CONVIÉRTETE EN CREADOR!</b>\n\n"
                "Como creador podrás:\n"
                "• 📸 Subir contenido exclusivo PPV\n"
                "• 💰 Establecer suscripciones mensuales\n"
                "• 📊 Gestionar tus catálogos\n"
                "• 💎 Ganar dinero con tus fans\n\n"
                "💫 La comisión de la plataforma es del 20%\n"
                "⭐️ Los pagos se procesan en Telegram Stars\n\n"
                "🚀 <b>¿Estás listo para empezar?</b>"
            )
            keyboard = get_creator_onboarding_menu()
        else:
            # Creador ya registrado - mostrar menú profesional con botones del TECLADO
            text = (
                f"🎨 <b>PANEL DE CREADOR</b>\n\n"
                f"¡Hola {creator[3]}! 👋\n\n"
                f"📊 <b>Tu perfil está activo</b>\n"
                f"💰 Precio de suscripción: {creator[4]} ⭐️\n"
                f"👥 Suscriptores activos: {creator[6] if len(creator) > 6 else 0}\n\n"
                f"💡 <i>Usa los botones del teclado de abajo para navegar.</i>"
            )
            keyboard = get_creator_menu()  # Usar teclado en lugar de inline
        
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
        keyboard = get_main_keyboard(message.from_user.id, username)
    
    await message.answer(text, reply_markup=keyboard)

# ==================== HANDLERS DEL MENÚ PRINCIPAL ====================

@router.message(F.text == "🎨 Ser Creador")
async def handle_ser_creador(message: Message, state: FSMContext):
    """Manejar selección de 'Ser Creador'"""
    print(f"🚀 DEBUG: Handler 'Ser Creador' ejecutado por usuario {message.from_user.id}")
    
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes usar el bot.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    
    if creator:
        # Ya es creador, mostrar menú de creador
        print(f"🚀 DEBUG: Usuario {message.from_user.id} es creador, navegando a CREATOR")
        await NavigationManager.push_state(MenuState.CREATOR, state)
        await show_menu(MenuState.CREATOR, message, state)
    else:
        # No es creador, pero navegamos al menú de creador que mostrará la información apropiada
        print(f"🚀 DEBUG: Usuario {message.from_user.id} NO es creador, navegando a CREATOR onboarding")
        await NavigationManager.push_state(MenuState.CREATOR, state)
        await show_menu(MenuState.CREATOR, message, state)

@router.message(F.text == "🔍 Explorar Creadores")
async def handle_explorar_creadores(message: Message, state: FSMContext):
    """Manejar selección de 'Explorar Creadores' - mostrar directamente los creadores"""
    print(f"🚀 DEBUG: Handler 'Explorar Creadores' ejecutado por usuario {message.from_user.id}")
    
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes usar el bot.")
        return
    
    # Solo hacer push del estado si no estamos ya en EXPLORE para evitar duplicados
    current_state = await NavigationManager.get_current_state(state)
    if current_state != MenuState.EXPLORE:
        await NavigationManager.push_state(MenuState.EXPLORE, state)
    
    # Siempre ejecutar explore_creators directamente, sin mensajes intermedios
    print(f"🚀 DEBUG: Ejecutando explore_creators directamente")
    from creator_handlers import explore_creators
    await explore_creators(message)

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

# ==================== HANDLERS DEL MENÚ CREATOR ONBOARDING ====================

@router.message(F.text == "✅ Registrarme como Creador")
async def handle_registrar_creador(message: Message, state: FSMContext):
    """Manejar selección de 'Registrarme como Creador'"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes registrarte como creador.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if creator:
        await message.answer("✅ Ya estás registrado como creador. Usa el menú para gestionar tu perfil.")
        return
    
    # Iniciar el flujo de registro directamente
    from creator_handlers import CreatorRegistration
    await message.answer(
        "🎨 <b>¡PERFECTO! INICIANDO REGISTRO</b>\n\n"
        "Vamos a configurar tu perfil de creador paso a paso.\n\n"
        "📝 <b>Paso 1 de 5: NOMBRE ARTÍSTICO</b>\n"
        "¿Cuál es tu nombre artístico o cómo quieres que te conozcan tus fans?\n\n"
        "💡 <i>Ejemplo: 'Sofia Creativa', 'El Chef Miguel', etc.</i>"
    )
    await state.set_state(CreatorRegistration.waiting_for_name)

@router.message(F.text == "ℹ️ Más Información")
async def handle_mas_informacion_creador(message: Message, state: FSMContext):
    """Manejar selección de 'Más Información' sobre ser creador"""
    await message.answer(
        "📋 <b>INFORMACIÓN DETALLADA PARA CREADORES</b>\n\n"
        "💰 <b>Ganancias:</b>\n"
        "• Conservas el 80% de todas las ventas\n"
        "• Plataforma retiene 20% de comisión\n"
        "• Retiro mínimo: 1000 ⭐️ (≈ $13 USD)\n\n"
        "📊 <b>Tipos de contenido:</b>\n"
        "• Suscripciones mensuales (incluso GRATIS)\n"
        "• Contenido PPV (pago por ver)\n"
        "• Propinas de tus fans\n\n"
        "⭐️ <b>Pagos seguros con Telegram Stars</b>\n"
        "• Procesamiento automático\n"
        "• Sin necesidad de cuentas bancarias\n"
        "• Conversión directa a dinero real\n\n"
        "🛡️ <b>Protección:</b>\n"
        "• Contenido protegido contra piratería\n"
        "• Sistema de moderación activo\n"
        "• Soporte técnico 24/7"
    )

# ==================== HANDLER PARA VOLVER ====================

@router.message(F.text == "⬅️ Volver")
async def handle_volver(message: Message, state: FSMContext):
    """Manejar botón 'Volver' - navegar al menú anterior"""
    previous_state = await NavigationManager.pop_state(state)
    await show_menu(previous_state, message, state)

# ==================== HANDLERS PARA PERFIL DE CREADOR PROFESIONAL ====================

@router.callback_query(F.data == "view_my_profile")
async def handle_view_my_profile(callback: CallbackQuery, state: FSMContext):
    """Manejar 'Ver Mi Perfil' - mostrar submenú de gestión"""
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.")
        return
    
    # Mostrar información del perfil y submenú de opciones
    profile_text = (
        f"👤 <b>MI PERFIL DE CREADOR</b>\n\n"
        f"🎨 <b>Nombre artístico:</b> {creator[3]}\n"
        f"📝 <b>Descripción:</b> {creator[2] if creator[2] else 'Sin descripción'}\n"
        f"💰 <b>Precio de suscripción:</b> {creator[4]} ⭐️\n"
        f"👥 <b>Suscriptores activos:</b> {creator[6] if len(creator) > 6 else 0}\n"
        f"📊 <b>Estado:</b> ✅ Perfil activo\n\n"
        f"💫 <b>¿Qué deseas gestionar?</b>"
    )
    
    await callback.message.edit_text(
        text=profile_text,
        reply_markup=get_creator_profile_submenu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Volver al menú principal"""
    await NavigationManager.reset_to_main(state)
    
    # Eliminar el mensaje inline actual
    try:
        await callback.message.delete()
    except Exception:
        pass  # Ignorar errores si el mensaje ya fue eliminado
    
    # Enviar nuevo mensaje con el menú principal (ReplyKeyboardMarkup)
    username = callback.from_user.username
    text = "🌟 <b>ONLYSTARS - MENÚ PRINCIPAL</b>\n\n¿Qué te gustaría hacer hoy?"
    keyboard = get_main_keyboard(callback.from_user.id, username)
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "back_to_creator_main")
async def handle_back_to_creator_main(callback: CallbackQuery, state: FSMContext):
    """Volver al menú principal de creador"""
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.")
        return
    
    text = (
        f"🎨 <b>PANEL DE CREADOR</b>\n\n"
        f"¡Hola {creator[3]}! 👋\n\n"
        f"📊 <b>Tu perfil está activo</b>\n"
        f"💰 Precio de suscripción: {creator[4]} ⭐️\n"
        f"👥 Suscriptores activos: {creator[6] if len(creator) > 6 else 0}\n\n"
        f"💫 <b>¿Qué deseas gestionar hoy?</b>"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_creator_profile_main_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_balance")
async def handle_profile_balance(callback: CallbackQuery, state: FSMContext):
    """Ver balance del creador"""
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.", show_alert=True)
        return
    
    from database import get_user_balance
    balance = get_user_balance(callback.from_user.id)
    
    balance_text = (
        f"💰 <b>MI BALANCE</b>\n\n"
        f"🌟 <b>Balance actual:</b> {balance} ⭐️\n"
        f"💵 <b>Equivalente USD:</b> ~${balance * 0.013:.2f}\n\n"
        f"📊 <b>Información:</b>\n"
        f"• Comisión de plataforma: 20%\n"
        f"• Retiro mínimo: 1000 ⭐️\n"
        f"• Tasa: $0.013 por estrella\n\n"
        f"💡 <b>¿Quieres retirar ganancias?</b> Usa el botón de abajo"
    )
    
    from keyboards import get_balance_keyboard
    await callback.message.edit_text(
        text=balance_text,
        reply_markup=get_balance_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_withdraw")
async def handle_profile_withdraw(callback: CallbackQuery, state: FSMContext):
    """Iniciar flujo de retiro guiado"""
    if is_user_banned(callback.from_user.id):
        await callback.answer("❌ Tu cuenta está baneada y no puedes retirar.", show_alert=True)
        return
    
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.", show_alert=True)
        return
    
    from database import get_user_balance
    import os
    
    balance = get_user_balance(callback.from_user.id)
    min_withdrawal = int(os.getenv("MIN_WITHDRAWAL", 1000))
    
    if balance < min_withdrawal:
        await callback.answer(
            f"❌ Balance insuficiente. Necesitas al menos {min_withdrawal} ⭐️ para retirar.\nTu balance actual: {balance} ⭐️",
            show_alert=True
        )
        return
    
    withdraw_text = (
        f"💸 <b>RETIRAR GANANCIAS</b>\n\n"
        f"💰 <b>Balance disponible:</b> {balance} ⭐️\n"
        f"💵 <b>Equivalente USD:</b> ~${balance * 0.013:.2f}\n\n"
        f"📊 <b>Información:</b>\n"
        f"• Retiro mínimo: {min_withdrawal} ⭐️\n"
        f"• Tasa: $0.013 por estrella\n\n"
        f"🔢 <b>Escribe la cantidad que quieres retirar:</b>\n"
        f"<i>Ejemplo: 1000 (o 'todo' para retirar todo)</i>"
    )
    
    from creator_handlers import WithdrawalFlow
    await callback.message.edit_text(withdraw_text)
    await state.set_state(WithdrawalFlow.waiting_for_amount)
    await callback.answer()

@router.callback_query(F.data == "profile_create_ppv")
async def handle_profile_create_ppv(callback: CallbackQuery, state: FSMContext):
    """Crear contenido PPV"""
    from creator_handlers import CreatePPVContent
    
    await callback.message.edit_text(
        "🎥 <b>CREAR CONTENIDO PPV</b>\n\n"
        "📸 Sube una foto o video que quieras monetizar.\n"
        "💰 Después podrás establecer el precio en Stars.\n\n"
        "📤 <b>Envía tu contenido ahora:</b>"
    )
    
    await state.set_state(CreatePPVContent.waiting_for_content)
    await callback.answer()

@router.callback_query(F.data == "profile_edit")
async def handle_profile_edit(callback: CallbackQuery, state: FSMContext):
    """Mostrar opciones de edición de perfil"""
    if is_user_banned(callback.from_user.id):
        await callback.answer("❌ Tu cuenta está baneada y no puedes editar tu perfil.", show_alert=True)
        return
    
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.", show_alert=True)
        return
    
    edit_text = (
        f"✏️ <b>EDITAR PERFIL</b>\n\n"
        f"🎨 <b>Nombre actual:</b> {creator[3]}\n"
        f"📝 <b>Descripción actual:</b> {creator[2] if creator[2] else 'Sin descripción'}\n"
        f"💰 <b>Precio actual:</b> {creator[4]} ⭐️\n\n"
        f"📝 <b>¿Qué quieres editar?</b>"
    )
    
    from keyboards import get_profile_edit_keyboard
    await callback.message.edit_text(
        text=edit_text,
        reply_markup=get_profile_edit_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "profile_catalog")
async def handle_profile_catalog(callback: CallbackQuery, state: FSMContext):
    """Ver catálogo personal"""
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.", show_alert=True)
        return
    
    from database import get_ppv_by_creator
    content_list = get_ppv_by_creator(callback.from_user.id)
    
    if not content_list:
        catalog_text = (
            f"📊 <b>MI CATÁLOGO</b>\n\n"
            f"📭 <b>No tienes contenido PPV aún</b>\n\n"
            f"💡 <b>¡Empieza a crear!</b>\n"
            f"Usa 'Crear Contenido PPV' para subir tu primer contenido y comenzar a ganar dinero.\n\n"
            f"🎯 <b>Tipos de contenido:</b>\n"
            f"• Fotos exclusivas\n"
            f"• Videos premium\n"
            f"• Álbumes temáticos"
        )
    else:
        catalog_text = f"📊 <b>MI CATÁLOGO</b>\n\n📈 <b>Total de contenido:</b> {len(content_list)} elementos\n\n"
        
        for i, content in enumerate(content_list[:5], 1):  # Mostrar máximo 5
            catalog_text += f"🎯 <b>{i}.</b> {content[3]} - {content[4]} ⭐️\n"
        
        if len(content_list) > 5:
            catalog_text += f"\n... y {len(content_list) - 5} más\n"
    
    await callback.message.edit_text(
        text=catalog_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎥 Crear Contenido PPV", callback_data="profile_create_ppv")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_creator_main")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "profile_stats")
async def handle_profile_stats(callback: CallbackQuery, state: FSMContext):
    """Ver estadísticas del creador"""
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Error: No se encontró tu perfil de creador.", show_alert=True)
        return
    
    from database import get_creator_stats, get_ppv_by_creator, get_user_balance
    
    balance = get_user_balance(callback.from_user.id)
    content_count = len(get_ppv_by_creator(callback.from_user.id))
    
    stats_text = (
        f"📈 <b>MIS ESTADÍSTICAS</b>\n\n"
        f"👤 <b>Perfil:</b> {creator[3]}\n"
        f"💰 <b>Precio suscripción:</b> {creator[4]} ⭐️\n"
        f"👥 <b>Suscriptores:</b> {creator[6] if len(creator) > 6 else 0}\n"
        f"🎯 <b>Contenido PPV:</b> {content_count} elementos\n"
        f"💎 <b>Balance actual:</b> {balance} ⭐️\n"
        f"💵 <b>Equivalente USD:</b> ~${balance * 0.013:.2f}\n\n"
        f"📊 <b>Estado del perfil:</b> ✅ Activo\n"
        f"📅 <b>Miembro desde:</b> {creator[9][:10] if len(creator) > 9 else 'N/A'}"
    )
    
    await callback.message.edit_text(
        text=stats_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Ver Balance Detallado", callback_data="profile_balance")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_creator_main")]
        ])
    )
    await callback.answer()