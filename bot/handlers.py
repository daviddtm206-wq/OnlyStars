# bot/handlers.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
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
    keyboard = get_main_keyboard(message.from_user.id, username)
    
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
    
    # Obtener contenido PPV del creador
    from database import get_ppv_by_creator, get_ppv_album_items
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.media_group import MediaGroupBuilder
    
    content_list = get_ppv_by_creator(message.from_user.id)
    
    if not content_list:
        await message.answer(
            f"📊 <b>MI CATÁLOGO PROFESIONAL</b>\n\n"
            f"📭 <b>No tienes contenido PPV aún</b>\n\n"
            f"💡 <b>¡Empieza a crear!</b>\n"
            f"Usa '📸 Crear PPV' para subir tu primer contenido y comenzar a ganar dinero.\n\n"
            f"🎯 <b>Tipos de contenido:</b>\n"
            f"• Fotos exclusivas\n"
            f"• Videos premium\n"
            f"• Álbumes temáticos"
        )
        return
    
    # Mensaje de encabezado profesional
    total_content = len(content_list)
    total_earnings = sum(content[4] for content in content_list)  # Suma de precios como estimado
    
    header_text = (
        f"📊 <b>MI CATÁLOGO PROFESIONAL</b>\n\n"
        f"📈 <b>Total de contenido:</b> {total_content} publicaciones\n"
        f"💰 <b>Valor del catálogo:</b> {total_earnings} ⭐️\n"
        f"👤 <b>Creador:</b> {creator[3]}\n\n"
        f"📱 <b>Vista como canal profesional:</b>"
    )
    
    await message.answer(header_text)
    
    # Mostrar cada contenido como post individual
    for index, content in enumerate(content_list, 1):
        content_id = content[0]
        creator_id = content[1]
        title = content[2]
        description = content[3]
        price_stars = content[4]
        file_id = content[5]
        file_type = content[6]
        album_type = content[7] if len(content) > 7 else 'single'
        
        # Construir caption profesional
        caption_text = f"📸 <b>Post #{index}</b>\n"
        if title and title.strip():
            caption_text += f"📝 <b>Título:</b> {title}\n"
        if description and description.strip():
            caption_text += f"💭 <b>Descripción:</b> {description}\n"
        caption_text += f"💰 <b>Precio:</b> {price_stars} ⭐️\n"
        caption_text += f"📊 <b>Tipo:</b> {'🎬 Álbum' if album_type == 'album' else '📷 Individual'}"
        
        # Botón de gestión: solo eliminar
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"delete_content_{content_id}")]
        ])
        
        try:
            if album_type == 'album':
                # Mostrar álbum completo
                album_items = get_ppv_album_items(content_id)
                if album_items:
                    media_group = MediaGroupBuilder(caption=caption_text)
                    for item in album_items:
                        item_file_id = item[2]  # file_id en ppv_album_items
                        item_file_type = item[3]  # file_type en ppv_album_items
                        
                        if item_file_type == "photo":
                            media_group.add_photo(media=item_file_id)
                        elif item_file_type == "video":
                            media_group.add_video(media=item_file_id)
                    
                    await message.bot.send_media_group(
                        chat_id=message.chat.id,
                        media=media_group.build()
                    )
                    
                    # Enviar botones por separado para álbumes
                    await message.bot.send_message(
                        chat_id=message.chat.id,
                        text="🎬 <b>Gestionar este álbum:</b>",
                        reply_markup=keyboard
                    )
                else:
                    # Fallback si no hay elementos del álbum
                    await message.answer(
                        f"🎬 <b>Álbum #{index} (Vacío)</b>\n\n{caption_text}",
                        reply_markup=keyboard
                    )
            else:
                # Contenido individual
                if file_type == "photo":
                    await message.bot.send_photo(
                        chat_id=message.chat.id,
                        photo=file_id,
                        caption=caption_text,
                        reply_markup=keyboard
                    )
                elif file_type == "video":
                    await message.bot.send_video(
                        chat_id=message.chat.id,
                        video=file_id,
                        caption=caption_text,
                        reply_markup=keyboard
                    )
                else:
                    # Fallback para tipos no soportados
                    await message.answer(
                        f"📄 <b>Contenido #{index}</b>\n\n{caption_text}",
                        reply_markup=keyboard
                    )
        
        except Exception as e:
            print(f"Error enviando contenido {content_id}: {e}")
            # Fallback: enviar como mensaje de texto
            await message.answer(
                f"📱 <b>Contenido #{index}</b>\n\n{caption_text}\n\n⚠️ Error al mostrar media",
                reply_markup=keyboard
            )
    
    # Mensaje final profesional
    await message.answer(
        f"✨ <b>Fin del catálogo</b>\n\n"
        f"📊 Se mostraron {total_content} contenidos\n"
        f"💡 Usa los botones en cada post para gestionar tu contenido"
    )

# Handlers para el botón de gestión de contenido del catálogo profesional

@router.callback_query(F.data.startswith("delete_content_"))
async def delete_content_callback(callback: CallbackQuery):
    await callback.answer()
    content_id = int(callback.data.split("_")[2])
    
    # Crear confirmación de eliminación
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar Eliminación", callback_data=f"confirm_delete_{content_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_delete")
        ]
    ])
    
    await callback.message.answer(
        f"🗑️ <b>Confirmar Eliminación</b>\n\n"
        f"¿Estás seguro de que quieres eliminar este contenido?\n\n"
        f"⚠️ <b>Esta acción no se puede deshacer</b>\n"
        f"• Se eliminará el contenido permanentemente\n"
        f"• Los usuarios que lo compraron perderán el acceso",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_callback(callback: CallbackQuery):
    await callback.answer()
    content_id = int(callback.data.split("_")[2])
    
    from database import delete_ppv_content
    success, message_text = delete_ppv_content(content_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Contenido Eliminado</b>\n\n"
            f"El contenido #{content_id} ha sido eliminado exitosamente.\n"
            f"Usa '📊 Mi Catálogo' para ver tu catálogo actualizado."
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Error al Eliminar</b>\n\n"
            f"{message_text}"
        )

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "❌ <b>Eliminación Cancelada</b>\n\n"
        "El contenido no ha sido eliminado."
    )


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
    keyboard = get_main_keyboard(message.from_user.id, username)
    
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
    keyboard = get_main_keyboard(message.from_user.id, username)
    
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

# Database is initialized in main.py

