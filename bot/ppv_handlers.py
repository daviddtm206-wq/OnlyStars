# bot/ppv_handlers.py
from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command
from database import (get_ppv_content, has_purchased_ppv, add_ppv_purchase, 
                     add_transaction, update_balance, is_user_banned)
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
    
    content_id, creator_id, title, description, price_stars, file_id, file_type, created_at = content
    
    # Verificar si el usuario ya compró este contenido
    if has_purchased_ppv(message.from_user.id, content_id):
        await message.answer("✅ Ya has comprado este contenido. Aquí está:")
        
        if file_type == "photo":
            await message.answer_photo(photo=file_id, caption=f"📸 {title}")
        elif file_type == "video":
            await message.answer_video(video=file_id, caption=f"🎬 {title}")
        return
    
    # Verificar si es el mismo creador
    if creator_id == message.from_user.id:
        await message.answer("❌ No puedes comprar tu propio contenido.")
        return
    
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Contenido PPV: {title}",
        description=description,
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