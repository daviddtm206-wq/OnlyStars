# bot/catalog_handlers.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, InputMediaVideo, LabeledPrice
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (get_creator_by_id, is_user_banned, get_active_subscriptions, 
                     get_ppv_by_creator, has_purchased_ppv, get_ppv_content, get_ppv_album_items,
                     add_ppv_purchase, add_transaction, update_balance)
import time
import os
import math

COMMISSION_PERCENTAGE = int(os.getenv("COMMISSION_PERCENTAGE", 20))

router = Router()

# Handler para procesar compras de Paid Media (CORREGIDO para usar paid_media_purchased)
@router.message(F.paid_media_purchased)
async def process_paid_media_purchase(message: Message):
    """Procesa compras exitosas de Paid Media desde el catálogo"""
    # IMPORTANTE: Este handler ahora usa paid_media_purchased (correcto para Paid Media)
    # Las compras por factura (/comprar_ppv) se manejan en ppv_handlers.py
    
    # Verificar si hay información de Paid Media tracking
    if hasattr(message.bot, '_paid_media_tracking'):
        # Buscar si este mensaje corresponde a una compra de Paid Media
        # En un bot real, esto se haría consultando una tabla en DB
        for message_id, tracking_info in message.bot._paid_media_tracking.items():
            if tracking_info['buyer_id'] == message.from_user.id:
                # Procesar la compra
                content_id = tracking_info['content_id']
                creator_id = tracking_info['creator_id']
                price_stars = tracking_info['price_stars']
                album_type = tracking_info['album_type']
                
                # Verificar si ya fue comprado (evitar duplicados) y usar return value seguro
                purchase_added = add_ppv_purchase(message.from_user.id, content_id)
                if purchase_added:
                    # Calcular comisión y ganancia del creador
                    # CRÍTICO: Asegurar comisión mínima para evitar fuga en montos pequeños
                    commission = max(1, math.ceil(price_stars * COMMISSION_PERCENTAGE / 100)) if price_stars > 0 else 0
                    creator_earnings = price_stars - commission
                    
                    # Actualizar balance del creador
                    update_balance(creator_id, creator_earnings)
                    
                    # Registrar transacción
                    add_transaction(message.from_user.id, creator_id, price_stars, commission, "ppv")
                    
                    # Confirmar compra al usuario
                    content_type = "📁 Álbum" if album_type == 'album' else "📸 Contenido"
                    await message.answer(
                        f"✅ <b>¡Compra exitosa via Paid Media!</b>\n\n"
                        f"💰 Pagaste: {price_stars} ⭐️\n"
                        f"📦 {content_type} desbloqueado\n\n"
                        f"💡 Ahora puedes ver este contenido en /mis_catalogos"
                    )
                else:
                    # Ya fue comprado, solo confirmar
                    await message.answer(
                        f"✅ <b>Contenido ya desbloqueado</b>\n\n"
                        f"💡 Puedes ver este contenido en /mis_catalogos"
                    )
                
                # Limpiar tracking
                del message.bot._paid_media_tracking[message_id]
                break

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
    
    # Crear botones para cada creador al que está suscrito (evitar duplicados)
    keyboard = []
    catalog_text = "🎬 <b>MIS CATÁLOGOS EXCLUSIVOS</b>\n\n"
    catalog_text += "Tienes acceso a los siguientes catálogos privados:\n\n"
    
    # Usar un set para evitar creadores duplicados
    seen_creators = set()
    
    for subscription in subscriptions:
        creator_id = subscription[2]  # creator_id está en la posición 2
        
        # Si ya hemos procesado este creador, saltarlo
        if creator_id in seen_creators:
            continue
            
        seen_creators.add(creator_id)
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
    
    # Mostrar el catálogo completo estilo canal
    await show_complete_catalog(callback, creator_id, display_name)

async def show_complete_catalog(callback: CallbackQuery, creator_id: int, creator_name: str):
    """Muestra el catálogo completo con Paid Media (precios superpuestos nativos)"""
    await callback.answer()
    
    # Obtener todo el contenido PPV del creador
    ppv_content = get_ppv_by_creator(creator_id)
    user_id = callback.from_user.id
    
    if not ppv_content:
        await callback.message.edit_text(
            f"💭 Este creador aún no ha publicado contenido PPV.\n\n"
            f"¡Mantente atento para nuevos contenidos exclusivos!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Volver a mis catálogos", callback_data="back_to_catalogs")]
            ])
        )
        return
    
    # Eliminar el mensaje anterior
    await callback.message.delete()
    
    # Mensaje de encabezado removido según solicitud del usuario
    
    # Enviar contenidos en orden cronológico (más antiguo primero, más reciente al final)
    # Ordenamiento defensivo por si acaso
    ppv_content = sorted(ppv_content, key=lambda r: r[0])  # Ordenar por ID ascendente
    
    print(f"🔍 Orden de envío: {[content[0] for content in ppv_content]}")  # Debug temporal
    
    for index, content in enumerate(ppv_content):
        content_id = content[0]
        position = index + 1  # Número de posición del más antiguo al más reciente
        
        if has_purchased_ppv(user_id, content_id):
            # Enviar contenido ya comprado
            await send_purchased_content_individual(callback, [content], f"✅ #{position} Contenido ya comprado")
        else:
            # Enviar contenido pagado
            await send_paid_content_individual(callback, [content], f"#{position} - {creator_name}")
        
        print(f"📤 Enviado contenido ID {content_id} como #{position}")  # Debug temporal
    
    # Mensaje final removido - solo mantener botones de navegación al final del último contenido

async def send_paid_content_individual(callback: CallbackQuery, paid_content: list, creator_name: str):
    """Envía cada contenido pagado individualmente con su precio específico usando sendPaidMedia nativo"""
    # Import error protection - handle ImportError for InputPaidMedia types
    try:
        from aiogram.types import InputPaidMediaPhoto, InputPaidMediaVideo
    except ImportError as e:
        print(f"❌ Error importando tipos de Paid Media: {e}")
        # Fallback to spoiler method for all content
        await send_content_album_fallback(callback, paid_content, "🔒 Contenido de pago - InputPaidMedia no disponible")
        return
    
    # Procesar cada contenido por separado con su precio específico
    for content in paid_content:
        content_id = content[0]
        title = content[2] 
        description = content[3]
        price_stars = content[4]
        file_id = content[5]
        file_type = content[6]
        album_type = content[7] if len(content) > 7 else 'single'  # Índice corregido para album_type
        
        try:
            paid_media_items = []
            
            # CRITICAL FIX: Handle albums as unified single messages
            if album_type == 'album':
                # Obtener todos los archivos del álbum
                album_items = get_ppv_album_items(content_id)
                
                if not album_items:
                    print(f"⚠️ Álbum {content_id} sin elementos - usando fallback")
                    await send_single_content_fallback(callback, [content], "🔒 Álbum vacío")
                    continue
                
                # Price consistency validation for albums
                # All album items should use the same unified price from the main content record
                validated_price = price_stars
                if validated_price <= 0:
                    print(f"⚠️ Precio inválido para álbum {content_id}: {validated_price}")
                    await send_single_content_fallback(callback, [content], "🔒 Precio inválido")
                    continue
                
                # Build paid media items for the entire album
                for item in album_items:
                    item_file_id = item[2]  # file_id en ppv_album_items
                    item_file_type = item[3]  # file_type en ppv_album_items
                    
                    if item_file_type == "photo":
                        paid_media_items.append(InputPaidMediaPhoto(media=item_file_id))
                    elif item_file_type == "video":
                        paid_media_items.append(InputPaidMediaVideo(media=item_file_id))
                
                # Send the ENTIRE album as ONE single paid media message with unified price
                if paid_media_items:
                    caption = description if description and description.strip() else None
                    
                    # Single call to send_paid_media for the entire album
                    paid_message = await callback.message.bot.send_paid_media(
                        chat_id=callback.message.chat.id,
                        star_count=validated_price,
                        media=paid_media_items,
                        caption=caption
                    )
                    
                    # Tracking verification - ensure tracking is saved correctly
                    if not hasattr(callback.message.bot, '_paid_media_tracking'):
                        callback.message.bot._paid_media_tracking = {}
                    
                    tracking_data = {
                        'content_id': content_id,
                        'creator_id': content[1],  # creator_id
                        'buyer_id': callback.from_user.id,
                        'price_stars': validated_price,
                        'album_type': album_type,
                        'timestamp': time.time(),  # CRÍTICO: Timestamp para correlación segura
                        'album_items_count': len(album_items)  # Para verificación adicional
                    }
                    
                    callback.message.bot._paid_media_tracking[paid_message.message_id] = tracking_data
                    
                    # Verify tracking was saved correctly
                    if paid_message.message_id in callback.message.bot._paid_media_tracking:
                        print(f"✅ Enviado álbum paid media {content_id}: {validated_price} ⭐️ ({len(album_items)} items)")
                    else:
                        print(f"⚠️ Error en tracking para álbum {content_id}")
                        
            else:
                # Contenido individual (compatibilidad hacia atrás)
                if file_type == "photo":
                    paid_media_items.append(InputPaidMediaPhoto(media=file_id))
                elif file_type == "video":
                    paid_media_items.append(InputPaidMediaVideo(media=file_id))
                
                # Send individual content as paid media
                if paid_media_items and price_stars > 0:
                    caption = description if description and description.strip() else None
                    
                    paid_message = await callback.message.bot.send_paid_media(
                        chat_id=callback.message.chat.id,
                        star_count=price_stars,
                        media=paid_media_items,
                        caption=caption
                    )
                    
                    # Tracking verification for individual content
                    if not hasattr(callback.message.bot, '_paid_media_tracking'):
                        callback.message.bot._paid_media_tracking = {}
                    
                    tracking_data = {
                        'content_id': content_id,
                        'creator_id': content[1],  # creator_id
                        'buyer_id': callback.from_user.id,
                        'price_stars': price_stars,
                        'album_type': album_type,
                        'timestamp': time.time()  # CRÍTICO: Timestamp para correlación segura
                    }
                    
                    callback.message.bot._paid_media_tracking[paid_message.message_id] = tracking_data
                    
                    # Verify tracking was saved correctly
                    if paid_message.message_id in callback.message.bot._paid_media_tracking:
                        print(f"✅ Enviado paid media individual {content_id}: {price_stars} ⭐️")
                    else:
                        print(f"⚠️ Error en tracking para contenido {content_id}")
                
        except Exception as e:
            # Solo usar fallback para este contenido específico si hay un error real
            print(f"⚠️ Error enviando paid media para contenido {content_id}: {e}")
            
            # Fallback individual para este contenido solamente
            await send_single_content_fallback(callback, [content], "🔒 Contenido de pago - Error con paid media")

async def send_purchased_content_individual(callback: CallbackQuery, purchased_content: list, caption_prefix: str):
    """Envía cada contenido ya comprado individualmente"""
    try:
        # Enviar cada contenido por separado, sin agrupar en álbumes
        for content in purchased_content:
            content_id = content[0]
            title = content[2]
            description = content[3]
            price_stars = content[4]  # Mostrar el precio original que se pagó
            file_id = content[5]
            file_type = content[6]
            album_type = content[7] if len(content) > 7 else 'single'  # Índice corregido para album_type
            
            caption = description if description and description.strip() else None
            
            # Si es un álbum, mostrar como media group
            if album_type == 'album':
                album_items = get_ppv_album_items(content_id)
                media_group = MediaGroupBuilder(caption=caption)
                
                for item in album_items:
                    item_file_id = item[2]  # file_id en ppv_album_items
                    item_file_type = item[3]  # file_type en ppv_album_items
                    
                    if item_file_type == "photo":
                        media_group.add_photo(media=item_file_id)
                    elif item_file_type == "video":
                        media_group.add_video(media=item_file_id)
                
                # Enviar álbum completo
                await callback.message.bot.send_media_group(
                    chat_id=callback.message.chat.id,
                    media=media_group.build()
                )
            else:
                # Contenido individual (compatibilidad hacia atrás)
                keyboard = [[InlineKeyboardButton(text="👁️ Ver contenido completo", callback_data=f"show_purchased_{content_id}")]]
                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                
                if file_type == "photo":
                    await callback.message.bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                elif file_type == "video":
                    await callback.message.bot.send_video(
                        chat_id=callback.message.chat.id,
                        video=file_id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                    
    except Exception as e:
        # Fallback a mensajes individuales si falla el envío
        await send_content_album_fallback(callback, purchased_content, caption_prefix)

async def send_single_content_fallback(callback: CallbackQuery, content_list: list, caption_prefix: str):
    """Fallback para un solo contenido con paid media error"""
    await send_content_album_fallback(callback, content_list, caption_prefix)

async def send_content_album_fallback(callback: CallbackQuery, content_list: list, caption_prefix: str):
    """Método fallback: envía contenidos como mensajes individuales con spoilers"""
    for index, content in enumerate(content_list):
        content_id = content[0]
        title = content[2]
        description = content[3]
        price_stars = content[4]
        file_id = content[5]
        file_type = content[6]
        
        # Verificar si ya está comprado
        already_purchased = has_purchased_ppv(callback.from_user.id, content_id)
        
        if already_purchased:
            caption = description if description and description.strip() else None
            keyboard = [[InlineKeyboardButton(text="👁️ Ver contenido completo", callback_data=f"show_purchased_{content_id}")]]
            has_spoiler = False
        else:
            caption = description if description and description.strip() else None
            keyboard = [[InlineKeyboardButton(text=f"🛒 Comprar por {price_stars} ⭐️", callback_data=f"buy_catalog_ppv_{content_id}")]]
            has_spoiler = True
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        try:
            if file_type == "photo":
                await callback.message.bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    has_spoiler=has_spoiler
                )
            elif file_type == "video":
                await callback.message.bot.send_video(
                    chat_id=callback.message.chat.id,
                    video=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    has_spoiler=has_spoiler
                )
        except Exception:
            # Último fallback: mensaje de texto
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=f"📱 <b>Contenido #{index + 1}: {title}</b>\n\n{caption}",
                reply_markup=reply_markup
            )

# Función de navegación eliminada - ya no es necesaria con el nuevo diseño de canal

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

async def process_ppv_purchase(user_id: int, content_id: int, bot, chat_id: int, message_id: int | None = None):
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

@router.callback_query(F.data == "explore_creators") 
async def explore_creators(callback: CallbackQuery):
    """Mostrar creadores disponibles para explorar"""
    await callback.answer()
    
    if not callback.from_user or not callback.message:
        return
    
    if is_user_banned(callback.from_user.id):
        await callback.message.edit_text("❌ Tu cuenta está baneada.")
        return
        
    # Mostrar lista de creadores disponibles
    from creator_handlers import show_available_creators
    await show_available_creators(callback.message, edit=True)