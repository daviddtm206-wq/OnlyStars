# bot/ppv_handlers.py
from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, SuccessfulPayment
from aiogram.filters import Command
from database import (get_ppv_content, has_purchased_ppv, add_ppv_purchase, 
                     add_transaction, update_balance, is_user_banned, get_ppv_album_items, get_creator_by_id)
from dotenv import load_dotenv
import os

load_dotenv()

router = Router()

COMMISSION_PERCENTAGE = int(os.getenv("COMMISSION_PERCENTAGE", 20))

@router.message(Command("comprar_ppv"))
async def buy_ppv_content(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Uso: /comprar_ppv &lt;ID_del_contenido&gt;\nEjemplo: /comprar_ppv 123")
        return
    
    try:
        content_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID de contenido inválido.")
        return
    
    content = get_ppv_content(content_id)
    if not content:
        await message.answer("❌ Contenido no encontrado.")
        return
    
    # Manejo flexible de la estructura de datos para compatibilidad
    if len(content) >= 8:
        content_id, creator_id, title, description, price_stars, file_id, file_type, album_type = content[:8]
    else:
        content_id, creator_id, title, description, price_stars, file_id, file_type = content[:7]
        album_type = 'single'  # Compatibilidad con registros antiguos
    
    # Verificar si el usuario ya compró este contenido
    if has_purchased_ppv(message.from_user.id, content_id):
        await message.answer("✅ Ya has comprado este contenido. Aquí está:")
        
        # Mostrar álbum o contenido individual según corresponda
        if album_type == 'album':
            from aiogram.utils.media_group import MediaGroupBuilder
            album_items = get_ppv_album_items(content_id)
            
            if album_items:
                media_group = MediaGroupBuilder(caption=f"📁 {title}")
                
                for item in album_items:
                    item_file_id = item[2]  # file_id en ppv_album_items
                    item_file_type = item[3]  # file_type en ppv_album_items
                    
                    if item_file_type == "photo":
                        media_group.add_photo(media=item_file_id)
                    elif item_file_type == "video":
                        media_group.add_video(media=item_file_id)
                
                await message.answer_media_group(media=media_group.build())
        else:
            # Contenido individual
            if file_type == "photo":
                await message.answer_photo(photo=file_id, caption=f"📸 {title}")
            elif file_type == "video":
                await message.answer_video(video=file_id, caption=f"🎬 {title}")
        return
    
    # Verificar si es el mismo creador
    if creator_id == message.from_user.id:
        await message.answer("❌ No puedes comprar tu propio contenido.")
        return
    
    # Determinar el tipo de contenido para el título de la factura
    content_type_label = "📁 Álbum" if album_type == 'album' else ("📸 Foto" if file_type == "photo" else "🎥 Video")
    
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=f"{content_type_label} PPV: {title}",
        description=description or "Contenido exclusivo",
        payload=f"ppv_{content_id}_{message.from_user.id}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Contenido PPV", amount=price_stars)],
        start_parameter=f"ppv_{content_id}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
        reply_to_message_id=message.message_id
    )

@router.message(Command("enviar_propina"))
async def send_tip(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer(
            "❌ Uso: /enviar_propina &lt;ID_creador&gt; &lt;monto&gt;\n"
            "Ejemplo: /enviar_propina 123456789 50"
        )
        return
    
    try:
        creator_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ ID del creador y monto deben ser números válidos.")
        return
    
    if amount <= 0:
        await message.answer("❌ El monto debe ser mayor a 0.")
        return
    
    # Verificar que el creador existe
    from database import get_creator_by_id
    creator = get_creator_by_id(creator_id)
    if not creator:
        await message.answer("❌ Creador no encontrado.")
        return
    
    if creator_id == message.from_user.id:
        await message.answer("❌ No puedes enviarte propinas a ti mismo.")
        return
    
    creator_name = creator[3]  # display_name
    
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Propina para {creator_name}",
        description=f"Enviar {amount} ⭐️ como propina",
        payload=f"tip_{creator_id}_{message.from_user.id}_{amount}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Propina", amount=amount)],
        start_parameter=f"tip_{creator_id}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
        reply_to_message_id=message.message_id
    )

# === CRITICAL PAYMENT PROCESSING HANDLERS ===

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Valida el pago antes de procesarlo"""
    payload = pre_checkout_query.invoice_payload
    
    if payload.startswith("ppv_"):
        # Validar compra PPV
        parts = payload.split("_")
        if len(parts) >= 3:
            content_id = int(parts[1])
            buyer_id = int(parts[2])
            
            # Verificar que el contenido aún existe
            content = get_ppv_content(content_id)
            if not content:
                await pre_checkout_query.answer(ok=False, error_message="Contenido no disponible")
                return
            
            # Verificar que el usuario no esté baneado
            if is_user_banned(buyer_id):
                await pre_checkout_query.answer(ok=False, error_message="Usuario baneado")
                return
            
            # Verificar que el usuario no haya comprado ya este contenido
            if has_purchased_ppv(buyer_id, content_id):
                await pre_checkout_query.answer(ok=False, error_message="Ya has comprado este contenido")
                return
    
    elif payload.startswith("tip_"):
        # Validar propina
        parts = payload.split("_")
        if len(parts) >= 4:
            creator_id = int(parts[1])
            tipper_id = int(parts[2])
            
            # Verificar que el creador existe
            creator = get_creator_by_id(creator_id)
            if not creator:
                await pre_checkout_query.answer(ok=False, error_message="Creador no encontrado")
                return
            
            # Verificar que el usuario no esté baneado
            if is_user_banned(tipper_id):
                await pre_checkout_query.answer(ok=False, error_message="Usuario baneado")
                return
    
    # Aprobar el pago
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Procesa pagos exitosos y entrega contenido"""
    payment: SuccessfulPayment = message.successful_payment
    payload = payment.invoice_payload
    amount_stars = payment.total_amount
    
    if payload.startswith("ppv_"):
        # Procesar compra PPV
        parts = payload.split("_")
        content_id = int(parts[1])
        buyer_id = int(parts[2])
        
        # Obtener información del contenido
        content = get_ppv_content(content_id)
        if not content:
            await message.answer("❌ Error: Contenido no encontrado")
            return
        
        # Manejo flexible de la estructura de datos para compatibilidad
        if len(content) >= 8:
            _, creator_id, title, description, price_stars, file_id, file_type, album_type = content[:8]
        else:
            _, creator_id, title, description, price_stars, file_id, file_type = content[:7]
            album_type = 'single'  # Compatibilidad con registros antiguos
        
        # Registrar la compra
        add_ppv_purchase(buyer_id, content_id)
        
        # Calcular comisión y ganancia del creador
        commission = (amount_stars * COMMISSION_PERCENTAGE) // 100
        creator_earnings = amount_stars - commission
        
        # Actualizar balance del creador
        update_balance(creator_id, creator_earnings)
        
        # Registrar transacción
        add_transaction(buyer_id, creator_id, amount_stars, commission, "ppv")
        
        # Entregar contenido al comprador
        await message.answer(f"✅ <b>¡Compra exitosa!</b>\n\n💰 Pagaste: {amount_stars} ⭐️\n\n📦 Tu contenido:")
        
        # Mostrar álbum o contenido individual según corresponda
        if album_type == 'album':
            from aiogram.utils.media_group import MediaGroupBuilder
            album_items = get_ppv_album_items(content_id)
            
            if album_items:
                media_group = MediaGroupBuilder(caption=f"📁 {title}\n📝 {description}" if description else f"📁 {title}")
                
                for item in album_items:
                    item_file_id = item[2]  # file_id en ppv_album_items
                    item_file_type = item[3]  # file_type en ppv_album_items
                    
                    if item_file_type == "photo":
                        media_group.add_photo(media=item_file_id)
                    elif item_file_type == "video":
                        media_group.add_video(media=item_file_id)
                
                await message.answer_media_group(media=media_group.build())
        else:
            # Contenido individual
            caption = f"📸 {title}\n📝 {description}" if description else f"📸 {title}"
            if file_type == "photo":
                await message.answer_photo(photo=file_id, caption=caption)
            elif file_type == "video":
                await message.answer_video(video=file_id, caption=caption)
    
    elif payload.startswith("tip_"):
        # Procesar propina
        parts = payload.split("_")
        creator_id = int(parts[1])
        tipper_id = int(parts[2])
        
        # Obtener información del creador
        creator = get_creator_by_id(creator_id)
        if not creator:
            await message.answer("❌ Error: Creador no encontrado")
            return
        
        creator_name = creator[3]  # display_name
        
        # Calcular comisión y ganancia del creador
        commission = (amount_stars * COMMISSION_PERCENTAGE) // 100
        creator_earnings = amount_stars - commission
        
        # Actualizar balance del creador
        update_balance(creator_id, creator_earnings)
        
        # Registrar transacción
        add_transaction(tipper_id, creator_id, amount_stars, commission, "tip")
        
        await message.answer(
            f"✅ <b>¡Propina enviada exitosamente!</b>\n\n"
            f"👤 Para: {creator_name}\n"
            f"💰 Monto: {amount_stars} ⭐️\n"
            f"💫 El creador ha recibido {creator_earnings} ⭐️ (después de comisión del {COMMISSION_PERCENTAGE}%)"
        )