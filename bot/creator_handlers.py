# bot/creator_handlers.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (add_creator, get_creator_by_id, get_all_creators, get_creator_stats, 
                     get_user_balance, withdraw_balance, add_ppv_content, is_user_banned)
from dotenv import load_dotenv
import os

load_dotenv()

router = Router()

class CreatorRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_payout = State()

class PPVCreation(StatesGroup):
    waiting_for_content = State()
    waiting_for_price = State()

@router.message(Command("convertirme_en_creador"))
async def start_creator_registration(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes registrarte como creador.")
        return
    
    # Verificar si ya es creador
    creator = get_creator_by_id(message.from_user.id)
    if creator:
        await message.answer("✅ Ya estás registrado como creador. Usa /mi_perfil para ver tu información.")
        return
    
    await message.answer(
        "🎨 ¡Perfecto! Vamos a registrarte como creador.\n\n"
        "Paso 1/5: ¿Cuál es tu nombre artístico?"
    )
    await state.set_state(CreatorRegistration.waiting_for_name)

@router.message(CreatorRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(display_name=message.text)
    await message.answer(
        "📝 Paso 2/5: Escribe una descripción de ti y tu contenido (máximo 200 caracteres):"
    )
    await state.set_state(CreatorRegistration.waiting_for_description)

@router.message(CreatorRegistration.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    if len(message.text) > 200:
        await message.answer("❌ La descripción es muy larga. Máximo 200 caracteres. Inténtalo de nuevo:")
        return
    
    await state.update_data(description=message.text)
    await message.answer(
        "💰 Paso 3/5: ¿Cuál será el precio de tu suscripción mensual? (en ⭐️ Stars)\n"
        "Ejemplo: 100"
    )
    await state.set_state(CreatorRegistration.waiting_for_price)

@router.message(CreatorRegistration.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido mayor a 0:")
        return
    
    await state.update_data(subscription_price=price)
    await message.answer(
        "📸 Paso 4/5: Envía tu foto de perfil (opcional). \n"
        "Puedes enviar una imagen o escribir 'saltar' para omitir este paso."
    )
    await state.set_state(CreatorRegistration.waiting_for_photo)

@router.message(CreatorRegistration.waiting_for_photo)
async def process_photo(message: Message, state: FSMContext):
    photo_url = None
    
    if message.photo:
        photo_url = message.photo[-1].file_id
    elif message.text and message.text.lower() != 'saltar':
        await message.answer("❌ Por favor envía una imagen o escribe 'saltar':")
        return
    
    await state.update_data(photo_url=photo_url)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Stars (Telegram)", callback_data="payout_stars")],
        [InlineKeyboardButton(text="💵 Dinero real", callback_data="payout_real")]
    ])
    
    await message.answer(
        "💳 Paso 5/5: ¿Cómo quieres recibir tus ganancias?",
        reply_markup=keyboard
    )
    await state.set_state(CreatorRegistration.waiting_for_payout)

@router.callback_query(F.data.in_(["payout_stars", "payout_real"]))
async def process_payout_method(callback: CallbackQuery, state: FSMContext):
    payout_method = "Stars" if callback.data == "payout_stars" else "Real"
    await state.update_data(payout_method=payout_method)
    
    # Obtener todos los datos y registrar al creador
    data = await state.get_data()
    
    try:
        add_creator(
            user_id=callback.from_user.id,
            username=callback.from_user.username or "",
            display_name=data['display_name'],
            description=data['description'],
            subscription_price=data['subscription_price'],
            photo_url=data.get('photo_url'),
            payout_method=data['payout_method']
        )
        
        await callback.message.edit_text(
            f"🎉 ¡Registro completado con éxito!\n\n"
            f"👤 Nombre artístico: {data['display_name']}\n"
            f"📝 Descripción: {data['description']}\n"
            f"💰 Precio suscripción: {data['subscription_price']} ⭐️\n"
            f"💳 Método de pago: {data['payout_method']}\n\n"
            f"✅ Ya puedes empezar a ganar dinero. Usa /mi_perfil para gestionar tu cuenta."
        )
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ Error al registrar tu cuenta. Inténtalo de nuevo más tarde."
        )
    
    await state.clear()

@router.message(Command("explorar_creadores"))
async def explore_creators(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creators = get_all_creators()
    
    if not creators:
        await message.answer("😔 Aún no hay creadores registrados en la plataforma.")
        return
    
    text = "🌟 **CREADORES DISPONIBLES**\n\n"
    
    for creator in creators[:10]:  # Mostrar máximo 10
        user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance, created_at = creator[1:10]
        
        text += f"👤 **{display_name}**\n"
        text += f"📝 {description}\n"
        text += f"💰 Suscripción: {subscription_price} ⭐️\n"
        text += f"🆔 ID: `{user_id}`\n\n"
        text += f"💫 Para suscribirte: `/suscribirme_a {user_id}`\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("mi_perfil"))
async def my_profile(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    
    if not creator:
        await message.answer(
            "❌ No estás registrado como creador.\n"
            "Usa /convertirme_en_creador para registrarte."
        )
        return
    
    user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance_stars, created_at = creator[1:10]
    
    subscribers_count = get_creator_stats(message.from_user.id)
    balance_usd = balance_stars * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = f"👤 **TU PERFIL DE CREADOR**\n\n"
    text += f"🎨 Nombre artístico: {display_name}\n"
    text += f"📝 Descripción: {description}\n"
    text += f"💰 Precio suscripción: {subscription_price} ⭐️\n"
    text += f"👥 Suscriptores activos: {subscribers_count}\n"
    text += f"💎 Balance: {balance_stars} ⭐️ (${balance_usd:.2f})\n"
    text += f"💳 Método de retiro: {payout_method}\n\n"
    text += f"🔧 Comandos disponibles:\n"
    text += f"• /balance - Ver saldo detallado\n"
    text += f"• /retirar <monto> - Retirar ganancias\n"
    text += f"• /crear_contenido_ppv - Crear contenido PPV"
    
    if photo_url:
        await message.answer_photo(photo=photo_url, caption=text, parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")

@router.message(Command("balance"))
async def check_balance(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    balance_stars = get_user_balance(message.from_user.id)
    balance_usd = balance_stars * float(os.getenv("EXCHANGE_RATE", 0.013))
    min_withdrawal = int(os.getenv("MIN_WITHDRAWAL", 1000))
    
    text = f"💎 **TU BALANCE**\n\n"
    text += f"⭐️ Balance en Stars: {balance_stars}\n"
    text += f"💵 Equivalente en USD: ${balance_usd:.2f}\n\n"
    text += f"💡 Retiro mínimo: {min_withdrawal} ⭐️\n\n"
    
    if balance_stars >= min_withdrawal:
        text += f"✅ Puedes retirar usando: `/retirar {balance_stars}`"
    else:
        text += f"❌ Necesitas al menos {min_withdrawal - balance_stars} ⭐️ más para retirar"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("retirar"))
async def withdraw(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Uso: /retirar <monto>\nEjemplo: /retirar 1000")
        return
    
    try:
        amount = int(args[1])
    except ValueError:
        await message.answer("❌ El monto debe ser un número válido.")
        return
    
    min_withdrawal = int(os.getenv("MIN_WITHDRAWAL", 1000))
    current_balance = get_user_balance(message.from_user.id)
    
    if amount < min_withdrawal:
        await message.answer(f"❌ El retiro mínimo es de {min_withdrawal} ⭐️")
        return
    
    if amount > current_balance:
        await message.answer(f"❌ No tienes suficiente balance. Tu balance actual: {current_balance} ⭐️")
        return
    
    if withdraw_balance(message.from_user.id, amount):
        amount_usd = amount * float(os.getenv("EXCHANGE_RATE", 0.013))
        await message.answer(
            f"✅ **Retiro procesado exitosamente**\n\n"
            f"💰 Monto retirado: {amount} ⭐️\n"
            f"💵 Equivalente: ${amount_usd:.2f}\n"
            f"💎 Balance restante: {current_balance - amount} ⭐️\n\n"
            f"🏦 El dinero será transferido según tu método de pago configurado."
        )
    else:
        await message.answer("❌ Error al procesar el retiro. Inténtalo de nuevo.")

@router.message(Command("crear_contenido_ppv"))
async def create_ppv_content(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ Solo los creadores registrados pueden crear contenido PPV.")
        return
    
    await message.answer(
        "📸 **CREAR CONTENIDO PPV**\n\n"
        "Envía la foto o video que quieres vender:"
    )
    await state.set_state(PPVCreation.waiting_for_content)

@router.message(PPVCreation.waiting_for_content)
async def process_ppv_content(message: Message, state: FSMContext):
    file_id = None
    file_type = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    else:
        await message.answer("❌ Por favor envía una foto o video:")
        return
    
    await state.update_data(file_id=file_id, file_type=file_type)
    await message.answer("💰 ¿Cuál será el precio de este contenido en ⭐️ Stars?")
    await state.set_state(PPVCreation.waiting_for_price)

@router.message(PPVCreation.waiting_for_price)
async def process_ppv_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Por favor ingresa un precio válido mayor a 0:")
        return
    
    data = await state.get_data()
    
    content_id = add_ppv_content(
        creator_id=message.from_user.id,
        title=f"Contenido PPV #{int(time.time())}",
        description="Contenido exclusivo",
        price_stars=price,
        file_id=data['file_id'],
        file_type=data['file_type']
    )
    
    await message.answer(
        f"✅ **Contenido PPV creado exitosamente**\n\n"
        f"🆔 ID del contenido: `{content_id}`\n"
        f"💰 Precio: {price} ⭐️\n\n"
        f"🔗 Los fans pueden comprarlo con:\n"
        f"`/comprar_ppv {content_id}`"
    )
    
    await state.clear()

import time