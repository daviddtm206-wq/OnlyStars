# bot/catalog_handlers.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, InputMediaVideo, LabeledPrice
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (get_creator_by_id, is_user_banned, get_active_subscriptions, 
                     get_ppv_by_creator, has_purchased_ppv, get_ppv_content)
import time

router = Router()

class CatalogStates(StatesGroup):
    viewing_catalog = State()
    browsing_creator_catalog = State()

async def build_catalogs_view(user_id: int) -> dict:
    """Construye la vista de catálogos para un usuario"""
    # Obtener suscripciones activas del usuario
    subscriptions = get_active_subscriptions(user_id)
    
    if not subscriptions:
        return {
            "text": (
                "📺 <b>MIS CATÁLOGOS EXCLUSIVOS</b>\n\n"
                "❌ Aún no tienes acceso a ningún catálogo.\n\n"
                "💡 Para acceder a catálogos:\n"
                "• Usa /explorar_creadores para ver creadores disponibles\n"
                "• Suscríbete con /suscribirme_a &lt;ID_creador&gt;\n"
                "• Una vez suscrito, podrás ver su catálogo privado aquí"
            ),
            "keyboard": None
        }
    
    # Crear botones para cada creador al que está suscrito
    keyboard = []
    catalog_text = "🎬 <b>MIS CATÁLOGOS EXCLUSIVOS</b>\n\n"
    catalog_text += "Tienes acceso a los siguientes catálogos privados:\n\n"
    
    for subscription in subscriptions:
        creator_id = subscription[2]  # creator_id está en la posición 2
        creator = get_creator_by_id(creator_id)
        
        if creator:
            display_name = creator[3]  # display_name está en la posición 3
            ppv_count = len(get_ppv_by_creator(creator_id))
            
            catalog_text += f"📺 <b>{display_name}</b> - {ppv_count} contenidos PPV\n"
            
            # Botón para ver el catálogo de este creador
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📺 Ver catálogo de {display_name}", 
                    callback_data=f"view_catalog_{creator_id}"
                )
            ])
    
    catalog_text += "\n💎 Selecciona un creador para ver su catálogo privado."
    
    return {
        "text": catalog_text,
        "keyboard": InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None
    }

@router.message(Command("mis_catalogos"))
async def show_my_catalogs(message: Message, state: FSMContext):
    """Muestra los catálogos de creadores a los que el usuario está suscrito"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    # Usar la función helper para construir la vista
    catalog_data = await build_catalogs_view(message.from_user.id)
    
    await message.answer(
        catalog_data["text"],
        reply_markup=catalog_data["keyboard"]
    )

@router.callback_query(F.data.startswith("view_catalog_"))
async def show_creator_catalog(callback: CallbackQuery, state: FSMContext):
    """Muestra el catálogo PPV de un creador específico"""
    await callback.answer()
    
    if not callback.message or not callback.from_user or not callback.data:
        return
        
    if is_user_banned(callback.from_user.id):
        await callback.message.edit_text("❌ Tu cuenta está baneada.")
        return
    
    # Extraer el creator_id del callback_data
    creator_id = int(callback.data.split("_")[2])
    
    # Verificar que el usuario tenga suscripción activa a este creador
    subscriptions = get_active_subscriptions(callback.from_user.id)
    has_subscription = any(sub[2] == creator_id for sub in subscriptions)
    
    if not has_subscription:
        try:
            await callback.message.edit_text(
                "❌ <b>Acceso denegado</b>\n\n"
                "Tu suscripción a este creador ha expirado o no tienes una suscripción activa.\n\n"
                "💡 Para acceder al catálogo, renueva tu suscripción usando:\n"
                f"/suscribirme_a {creator_id}"
            )
        except Exception:
            pass
        return
    
    # Obtener información del creador
    creator = get_creator_by_id(creator_id)
    if not creator:
        try:
            await callback.message.edit_text("❌ Creador no encontrado.")
        except Exception:
            pass
        return
    
    display_name = creator[3]
    
    # Obtener contenido PPV del creador
    ppv_content = get_ppv_by_creator(creator_id)
    
    if not ppv_content:
        try:
            await callback.message.edit_text(
                f"📺 <b>CATÁLOGO DE {display_name}</b>\n"
                f"(Solo para suscriptores)\n\n"
                f"💭 Este creador aún no ha publicado contenido PPV.\n\n"
                f"¡Mantente atento para nuevos contenidos exclusivos!"
            )
        except Exception:
            pass
        return
    
    # Mostrar el primer contenido del catálogo
    await show_catalog_content(callback.message, creator_id, 0, edit=True)

async def show_catalog_content(message, creator_id: int, content_index: int, edit: bool = False):
    """Muestra un contenido específico del catálogo con navegación"""
    creator = get_creator_by_id(creator_id)
    display_name = creator[3] if creator else "Creador"
    
    ppv_content = get_ppv_by_creator(creator_id)
    
    if content_index >= len(ppv_content) or content_index < 0:
        content_index = 0
    
    content = ppv_content[content_index]
    content_id = content[0]
    title = content[2]
    description = content[3]
    price_stars = content[4]
    file_id = content[5]
    file_type = content[6]
    
    # Verificar si el usuario ya compró este contenido
    user_id = message.chat.id
    already_purchased = has_purchased_ppv(user_id, content_id)
    
    # Texto del mensaje
    catalog_text = f"📺 <b>CATÁLOGO DE {display_name}</b>\n"
    catalog_text += f"(Solo para suscriptores)\n\n"
    catalog_text += f"💎 <b>{title}</b>\n"
    catalog_text += f"📝 {description}\n"
    catalog_text += f"💰 Precio: {price_stars} ⭐️\n\n"
    catalog_text += f"📊 Contenido {content_index + 1} de {len(ppv_content)}\n\n"
    
    if already_purchased:
        catalog_text += "✅ <b>YA COMPRADO</b> - Ver contenido abajo"
    else:
        catalog_text += "🔒 <b>Contenido bloqueado</b> - Compra para ver\n\n"
        if file_type == "photo":
            catalog_text += "📸 <i>Imagen Premium</i>"
        elif file_type == "video":
            catalog_text += "🎬 <i>Video Premium</i>"
    
    # Crear teclado de navegación
    keyboard = []
    
    # Fila de navegación
    nav_buttons = []
    if content_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"catalog_nav_{creator_id}_{content_index-1}"))
    if content_index < len(ppv_content) - 1:
        nav_buttons.append(InlineKeyboardButton(text="Siguiente ➡️", callback_data=f"catalog_nav_{creator_id}_{content_index+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Botón de compra/ver contenido
    if already_purchased:
        keyboard.append([InlineKeyboardButton(text="👁️ Ver contenido", callback_data=f"show_purchased_{content_id}")])
    else:
        keyboard.append([InlineKeyboardButton(text=f"🛒 Comprar por {price_stars} ⭐️", callback_data=f"buy_catalog_ppv_{content_id}")])
    
    # Botón para volver a la lista de catálogos
    keyboard.append([InlineKeyboardButton(text="📚 Volver a mis catálogos", callback_data="back_to_catalogs")])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    # CRITICAL BUG FIX: Detectar transición de media a texto
    is_target_text_only = not already_purchased
    is_current_media = edit and (hasattr(message, 'photo') or hasattr(message, 'video'))
    needs_delete_and_send = is_current_media and is_target_text_only
    
    try:
        if already_purchased:
            # Si ya compró el contenido, mostrar con la imagen/video visible
            if file_type == "photo":
                if edit:
                    # No se puede editar un mensaje de texto a imagen, enviar nuevo
                    await message.delete()
                    await message.bot.send_photo(
                        chat_id=message.chat.id,
                        photo=file_id,
                        caption=catalog_text,
                        reply_markup=reply_markup
                    )
                else:
                    await message.bot.send_photo(
                        chat_id=message.chat.id,
                        photo=file_id,
                        caption=catalog_text,
                        reply_markup=reply_markup
                    )
            elif file_type == "video":
                if edit:
                    await message.delete()
                    await message.bot.send_video(
                        chat_id=message.chat.id,
                        video=file_id,
                        caption=catalog_text,
                        reply_markup=reply_markup
                    )
                else:
                    await message.bot.send_video(
                        chat_id=message.chat.id,
                        video=file_id,
                        caption=catalog_text,
                        reply_markup=reply_markup
                    )
        else:
            # SECURITY FIX: Para contenido no comprado, NUNCA enviar el file_id real
            # Solo mostrar texto descriptivo + botón de compra para evitar bypass del paywall
            if edit and needs_delete_and_send:
                # CRITICAL FIX: Transición de media a texto requiere delete + send
                await message.delete()
                await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=catalog_text,
                    reply_markup=reply_markup
                )
            elif edit:
                # Transición texto a texto - se puede usar edit_text
                await message.edit_text(catalog_text, reply_markup=reply_markup)
            else:
                # Nuevo mensaje
                await message.answer(catalog_text, reply_markup=reply_markup)
    except Exception as e:
        # Si hay error, usar fallback con delete + send
        try:
            if edit:
                # Fallback: intentar delete + send si edit falla
                await message.delete()
                await message.bot.send_message(
                    chat_id=message.chat.id,
                    text=catalog_text,
                    reply_markup=reply_markup
                )
            else:
                await message.answer(catalog_text, reply_markup=reply_markup)
        except Exception as e2:
            # Último recurso: mensaje simple sin botones
            await message.bot.send_message(
                chat_id=message.chat.id,
                text="❌ Error mostrando el catálogo. Usa /mis_catalogos para reintentar."
            )

@router.callback_query(F.data.startswith("catalog_nav_"))
async def navigate_catalog(callback: CallbackQuery):
    """Navegar por el catálogo de un creador"""
    await callback.answer()
    
    if not callback.from_user:
        return
        
    if is_user_banned(callback.from_user.id):
        await callback.message.edit_text("❌ Tu cuenta está baneada.")
        return
    
    parts = callback.data.split("_")
    creator_id = int(parts[2])
    content_index = int(parts[3])
    
    # Verificar que el usuario tenga suscripción activa a este creador
    subscriptions = get_active_subscriptions(callback.from_user.id)
    has_subscription = any(sub[2] == creator_id for sub in subscriptions)
    
    if not has_subscription:
        await callback.message.edit_text(
            "❌ <b>Acceso denegado</b>\n\n"
            "Tu suscripción a este creador ha expirado o no tienes una suscripción activa.\n\n"
            "💡 Para acceder al catálogo, renueva tu suscripción usando:\n"
            f"/suscribirme_a {creator_id}"
        )
        return
    
    await show_catalog_content(callback.message, creator_id, content_index, edit=True)

@router.callback_query(F.data.startswith("show_purchased_"))
async def show_purchased_content(callback: CallbackQuery):
    """Muestra contenido ya comprado sin spoiler"""
    await callback.answer()
    
    content_id = int(callback.data.split("_")[2])
    
    # Verificar que realmente haya comprado el contenido
    if not has_purchased_ppv(callback.from_user.id, content_id):
        await callback.message.answer("❌ No has comprado este contenido.")
        return
    
    content = get_ppv_content(content_id)
    if not content:
        await callback.message.answer("❌ Contenido no encontrado.")
        return
    
    content_id, creator_id, title, description, price_stars, file_id, file_type, created_at = content
    
    caption = f"✅ <b>{title}</b>\n\n📝 {description}\n\n💎 Contenido comprado"
    
    try:
        if file_type == "photo":
            await callback.message.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=file_id,
                caption=caption
            )
        elif file_type == "video":
            await callback.message.bot.send_video(
                chat_id=callback.message.chat.id,
                video=file_id,
                caption=caption
            )
    except Exception as e:
        await callback.message.answer(f"✅ <b>{title}</b>\n\n📝 {description}\n\n❌ Error mostrando el contenido multimedia.")

async def process_ppv_purchase(user_id: int, content_id: int, bot, chat_id: int, message_id: int = None):
    """Función reutilizable para procesar compras de contenido PPV"""
    if is_user_banned(user_id):
        await bot.send_message(chat_id, "❌ Tu cuenta está baneada.")
        return
    
    content = get_ppv_content(content_id)
    if not content:
        await bot.send_message(chat_id, "❌ Contenido no encontrado.")
        return
    
    content_id, creator_id, title, description, price_stars, file_id, file_type, created_at = content
    
    # Verificar si el usuario ya compró este contenido
    if has_purchased_ppv(user_id, content_id):
        await bot.send_message(chat_id, "✅ Ya has comprado este contenido. Usa el botón 'Ver contenido' para acceder a él.")
        return
    
    # Verificar si es el mismo creador
    if creator_id == user_id:
        await bot.send_message(chat_id, "❌ No puedes comprar tu propio contenido.")
        return
    
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"Contenido PPV: {title}",
        description=description,
        payload=f"ppv_{content_id}_{user_id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Contenido PPV", amount=price_stars)],
        start_parameter=f"ppv_{content_id}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
        reply_to_message_id=message_id
    )

@router.callback_query(F.data.startswith("buy_catalog_ppv_"))
async def buy_catalog_ppv(callback: CallbackQuery):
    """Comprar contenido PPV desde el catálogo"""
    await callback.answer()
    
    if not callback.from_user or not callback.message:
        return
    
    content_id = int(callback.data.split("_")[3])
    
    # Usar la función reutilizable para procesar la compra
    await process_ppv_purchase(
        user_id=callback.from_user.id,
        content_id=content_id,
        bot=callback.message.bot,
        chat_id=callback.message.chat.id
    )

@router.callback_query(F.data == "back_to_catalogs")
async def back_to_catalogs(callback: CallbackQuery):
    """Volver a la lista de catálogos"""
    await callback.answer()
    
    if not callback.from_user or not callback.message:
        return
    
    if is_user_banned(callback.from_user.id):
        await callback.message.edit_text("❌ Tu cuenta está baneada.")
        return
    
    # Crear la vista de catálogos directamente
    catalog_data = await build_catalogs_view(callback.from_user.id)
    
    # CRITICAL FIX: Detectar si el mensaje actual es media para evitar edit_text fallido
    # El destino siempre es texto (listado de catálogos), detectar si origen es media
    is_current_media = hasattr(callback.message, 'photo') or hasattr(callback.message, 'video')
    needs_delete_and_send = is_current_media  # El destino siempre es texto
    
    try:
        if needs_delete_and_send:
            # PROACTIVE FIX: Si es media→texto, usar delete+send directamente
            await callback.message.delete()
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=catalog_data["text"],
                reply_markup=catalog_data["keyboard"]
            )
        else:
            # Transición texto→texto, se puede usar edit_text
            await callback.message.edit_text(
                catalog_data["text"],
                reply_markup=catalog_data["keyboard"]
            )
    except Exception:
        # Fallback: si cualquier operación falla, usar delete + send
        try:
            await callback.message.delete()
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=catalog_data["text"],
                reply_markup=catalog_data["keyboard"]
            )
        except Exception:
            # Último recurso: mensaje simple
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text="📺 Volver a /mis_catalogos para ver tus catálogos."
            )