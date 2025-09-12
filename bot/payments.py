# bot/payments.py
from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.filters import Command
from database import (add_transaction, update_balance, add_subscriber, get_creator_by_id, 
                     is_user_banned, get_ppv_content, add_ppv_purchase)
import asyncio
import time
from dotenv import load_dotenv
import os

load_dotenv()

router = Router()

COMMISSION_PERCENTAGE = int(os.getenv("COMMISSION_PERCENTAGE", 20))
EXCHANGE_RATE = float(os.getenv("EXCHANGE_RATE", 0.013))

@router.message(Command("suscribirme_a"))
async def subscribe_to_creator(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Uso: /suscribirme_a <ID_del_creador>\nEjemplo: /suscribirme_a 123456789")
        return

    try:
        creator_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID de creador inválido.")
        return

    creator = get_creator_by_id(creator_id)
    if not creator:
        await message.answer("❌ Creador no encontrado.")
        return
    
    if creator_id == message.from_user.id:
        await message.answer("❌ No puedes suscribirte a tu propio perfil.")
        return

    subscription_price_stars = creator[5]  # Índice 5 = subscription_price en la DB

    # Si la suscripción es gratuita (0 estrellas), crear suscripción directamente
    if subscription_price_stars == 0:
        expires_at = int(time.time()) + 30 * 24 * 60 * 60
        add_subscriber(message.from_user.id, creator_id, expires_at)
        
        await message.answer(
            f"🎉 <b>¡Suscripción GRATUITA exitosa a {creator[3]}!</b>\n\n"
            f"✅ ¡Ya tienes acceso al contenido exclusivo por 30 días!\n"
            f"💡 Usa /mis_catalogos para ver su catálogo privado."
        )
        return

    # Si tiene costo, enviar factura normal
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Suscripción a {creator[3]}",
        description=f"Acceso por 30 días a contenido exclusivo.",
        payload=f"sub_{creator_id}_{message.from_user.id}",
        provider_token="",  # Vacío para Stars
        currency="XTR",
        prices=[LabeledPrice(label="Suscripción Mensual", amount=subscription_price_stars)],
        start_parameter=f"creator_{creator_id}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
        reply_to_message_id=message.message_id
    )

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Handler específico para suscripciones - PPV se maneja en ppv_handlers.py"""
    payload = pre_checkout_query.invoice_payload
    
    # Solo manejar suscripciones, dejar PPV y propinas a ppv_handlers.py
    if payload.startswith("sub_"):
        await pre_checkout_query.answer(ok=True)
    # No hacer nada si es PPV o propina - lo maneja ppv_handlers.py

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Handler EXCLUSIVO para suscripciones - PPV y propinas se manejan en ppv_handlers.py"""
    payment = message.successful_payment
    payload = payment.invoice_payload  # Ej: "sub_12345_67890"
    amount_stars = payment.total_amount
    payer_id = message.from_user.id

    parts = payload.split("_")
    payment_type = parts[0]
    
    # SOLO manejar suscripciones aquí - el resto lo maneja ppv_handlers.py
    if payment_type == "sub":
        await handle_subscription_payment(message, parts, amount_stars, payer_id)
    # PPV y propinas se manejan en ppv_handlers.py para evitar conflictos

async def handle_subscription_payment(message, parts, amount_stars, payer_id):
    if len(parts) < 3:
        await message.answer("❌ Error en la transacción.")
        return
    
    try:
        creator_id = int(parts[1])
        payer_id_confirmed = int(parts[2])
    except ValueError:
        await message.answer("❌ Error en los datos de la transacción.")
        return
    
    if payer_id != payer_id_confirmed:
        await message.answer("❌ Error: ID de pagador no coincide.")
        return
    
    commission_stars = int(amount_stars * COMMISSION_PERCENTAGE / 100)
    creator_earnings = amount_stars - commission_stars
    
    add_transaction(payer_id, creator_id, creator_earnings, commission_stars, "subscription")
    update_balance(creator_id, creator_earnings)
    
    expires_at = int(time.time()) + 30 * 24 * 60 * 60
    add_subscriber(payer_id, creator_id, expires_at)
    
    creator = get_creator_by_id(creator_id)
    creator_name = creator[3] if creator else "Creador"
    
    await message.answer(
        f"🎉 ¡Suscripción exitosa a {creator_name}!\n\n"
        f"💰 Pagaste: {amount_stars} ⭐️\n"
        f"📝 Comisión de plataforma: {commission_stars} ⭐️\n"
        f"💎 Ganancia del creador: {creator_earnings} ⭐️\n\n"
        f"✅ ¡Ya tienes acceso al contenido exclusivo por 30 días!"
    )

# ELIMINADO: handle_ppv_payment y handle_tip_payment 
# Estas funciones se movieron COMPLETAMENTE a ppv_handlers.py para evitar conflictos
# TODOS los pagos PPV y propinas se manejan exclusivamente en ppv_handlers.py
