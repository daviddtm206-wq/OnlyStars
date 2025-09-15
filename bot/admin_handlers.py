# bot/creator_handlers_fixed.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (add_creator, get_creator_by_id, get_all_creators, get_creator_stats, 
                     get_user_balance, withdraw_balance, add_ppv_content, is_user_banned,
                     update_creator_display_name, update_creator_description, 
                     update_creator_subscription_price, update_creator_photo,
                     add_ppv_album_item, get_ppv_content_with_stats, delete_ppv_content,
                     get_ppv_content, get_ppv_album_items)
from dotenv import load_dotenv
import os
import time

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
    waiting_for_more_content = State()
    waiting_for_price = State()
    waiting_for_description = State()

class ProfileEdit(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_new_description = State()
    waiting_for_new_price = State()
    waiting_for_new_photo = State()
class CatalogManagement(StatesGroup):
    viewing_catalog = State()
    confirming_deletion = State()

@router.message(Command("convertirme_en_creador"))
async def start_creator_registration(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada y no puedes registrarte como creador.")
        return
    
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
        "💡 Puedes poner 0 para suscripciones gratuitas\n"
        "Ejemplo: 100 (o 0 para gratis)"
    )
    await state.set_state(CreatorRegistration.waiting_for_price)

@router.message(CreatorRegistration.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido (0 o mayor):")
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
    
    text = "🌟 <b>CREADORES DISPONIBLES</b>\n\n"
    
    for creator in creators[:10]:
        user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance, created_at = creator[1:10]
        
        text += f"👤 <b>{display_name}</b>\n"
        text += f"📝 {description}\n"
        text += f"💰 Suscripción: {subscription_price} ⭐️\n"
        text += f"🆔 ID: <code>{user_id}</code>\n\n"
        text += f"💫 Para suscribirte: <code>/suscribirme_a {user_id}</code>\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    await message.answer(text)

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
    
    text = f"👤 <b>TU PERFIL DE CREADOR</b>\n\n"
    text += f"🎨 Nombre artístico: {display_name}\n"
    text += f"📝 Descripción: {description}\n"
    text += f"💰 Precio suscripción: {subscription_price} ⭐️\n"
    text += f"👥 Suscriptores activos: {subscribers_count}\n"
    text += f"💎 Balance: {balance_stars} ⭐️ (${balance_usd:.2f})\n"
    text += f"💳 Método de retiro: {payout_method}\n\n"
    text += f"🔧 Comandos disponibles:\n"
    text += f"• /balance - Ver saldo detallado\n"
    text += f"• /retirar &lt;monto&gt; - Retirar ganancias\n"
    text += f"• /crear_contenido_ppv - Crear contenido PPV\n"
    text += f"• /mi_catalogo - Gestionar mi catálogo\n"
    text += f"• /editar_perfil - Editar información del perfil"
    
    if photo_url:
        await message.answer_photo(photo=photo_url, caption=text)
    else:
        await message.answer(text)

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
    
    text = f"💎 <b>TU BALANCE</b>\n\n"
    text += f"⭐️ Balance en Stars: {balance_stars}\n"
    text += f"💵 Equivalente en USD: ${balance_usd:.2f}\n\n"
    text += f"💡 Retiro mínimo: {min_withdrawal} ⭐️\n\n"
    
    if balance_stars >= min_withdrawal:
        text += f"✅ Puedes retirar usando: <code>/retirar {balance_stars}</code>"
    else:
        text += f"❌ Necesitas al menos {min_withdrawal - balance_stars} ⭐️ más para retirar"
    
    await message.answer(text)

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
        await message.answer("❌ Uso: /retirar &lt;monto&gt;\nEjemplo: /retirar 1000")
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
            f"✅ <b>Retiro procesado exitosamente</b>\n\n"
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
        "📸 <b>CREAR CONTENIDO PPV</b>\n\n"
        "Envía la primera foto o video de tu álbum:\n\n"
        "💡 <i>Podrás agregar más fotos/videos después</i>"
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
    
    # Inicializar lista de archivos en el álbum
    await state.update_data(album_files=[{'file_id': file_id, 'file_type': file_type}])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Agregar más fotos/videos", callback_data="add_more_content")],
        [InlineKeyboardButton(text="✅ Continuar con este archivo", callback_data="finish_content")]
    ])
    
    content_type = "📸 Foto" if file_type == "photo" else "🎥 Video"
    await message.answer(
        f"✅ {content_type} agregada al álbum\n\n"
        f"¿Quieres agregar más contenido a este álbum?",
        reply_markup=keyboard
    )
    await state.set_state(PPVCreation.waiting_for_more_content)

@router.callback_query(F.data == "add_more_content")
async def add_more_content(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    album_files = data.get('album_files', [])
    
    await callback.message.edit_text(
        f"📁 <b>ÁLBUM PPV ({len(album_files)} archivos)</b>\n\n"
        f"Envía otra foto o video para agregar al álbum:"
    )
    await state.set_state(PPVCreation.waiting_for_more_content)

@router.callback_query(F.data == "finish_content")
async def finish_content(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💰 ¿Cuál será el precio de este contenido en ⭐️ Stars?")
    await state.set_state(PPVCreation.waiting_for_price)

@router.message(PPVCreation.waiting_for_more_content)
async def process_more_content(message: Message, state: FSMContext):
    file_id = None
    file_type = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    else:
        await message.answer("❌ Por favor envía una foto o video, o usa los botones para continuar:")
        return
    
    # Agregar archivo a la lista
    data = await state.get_data()
    album_files = data.get('album_files', [])
    album_files.append({'file_id': file_id, 'file_type': file_type})
    await state.update_data(album_files=album_files)
    
    # Limitar a 10 archivos por álbum
    if len(album_files) >= 10:
        await message.answer(
            f"📁 <b>ÁLBUM COMPLETO ({len(album_files)} archivos)</b>\n\n"
            f"Has alcanzado el límite máximo de 10 archivos por álbum.\n\n"
            f"💰 ¿Cuál será el precio de este álbum en ⭐️ Stars?"
        )
        await state.set_state(PPVCreation.waiting_for_price)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Agregar más fotos/videos", callback_data="add_more_content")],
        [InlineKeyboardButton(text="✅ Finalizar álbum", callback_data="finish_content")]
    ])
    
    content_type = "📸 Foto" if file_type == "photo" else "🎥 Video"
    await message.answer(
        f"✅ {content_type} agregada al álbum\n\n"
        f"📁 <b>Archivos actuales: {len(album_files)}</b>\n"
        f"¿Quieres agregar más contenido?",
        reply_markup=keyboard
    )

@router.message(PPVCreation.waiting_for_price)
async def process_ppv_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Por favor ingresa un precio válido mayor a 0:")
        return
    
    await state.update_data(price=price)
    await message.answer(
        "📝 <b>Descripción opcional</b>\n\n"
        "Escribe una descripción personalizada para tu contenido o envía /saltar para omitir:\n\n"
        "Ejemplo: 'Mi nuevo set de fotos en lencería roja 🔥'"
    )
    await state.set_state(PPVCreation.waiting_for_description)

@router.message(PPVCreation.waiting_for_description)
async def process_ppv_description(message: Message, state: FSMContext):
    data = await state.get_data()
    album_files = data.get('album_files', [])
    
    # Si el usuario envía /saltar, usar descripción vacía
    if message.text and message.text.lower() == '/saltar':
        description = ""
    else:
        description = message.text or ""
    
    # Determinar si es álbum o contenido individual
    if len(album_files) > 1:
        # Crear álbum
        content_id = add_ppv_content(
            creator_id=message.from_user.id,
            title=f"Álbum PPV #{int(time.time())}",
            description=description,
            price_stars=data['price'],
            album_type='album'
        )
        
        # Agregar todos los archivos al álbum
        for i, file_data in enumerate(album_files):
            add_ppv_album_item(
                album_id=content_id,
                file_id=file_data['file_id'],
                file_type=file_data['file_type'],
                order_position=i
            )
        
        content_type = f"📁 Álbum ({len(album_files)} archivos)"
    else:
        # Crear contenido individual (compatibilidad con versión anterior)
        file_data = album_files[0]
        content_id = add_ppv_content(
            creator_id=message.from_user.id,
            title=f"Contenido PPV #{int(time.time())}",
            description=description,
            price_stars=data['price'],
            file_id=file_data['file_id'],
            file_type=file_data['file_type'],
            album_type='single'
        )
        
        content_type = "📸 Foto" if file_data['file_type'] == "photo" else "🎥 Video"
    
    if description:
        desc_preview = f"📝 Descripción: {description[:50]}{'...' if len(description) > 50 else ''}\n"
    else:
        desc_preview = "📝 Sin descripción personalizada\n"
    
    await message.answer(
        f"✅ <b>{content_type} creado exitosamente</b>\n\n"
        f"🆔 ID del contenido: <code>{content_id}</code>\n"
        f"💰 Precio: {data['price']} ⭐️\n"
        f"{desc_preview}\n"
        f"🔗 Los fans pueden comprarlo con:\n"
        f"<code>/comprar_ppv {content_id}</code>"
    )
    
    await state.clear()

@router.message(Command("editar_perfil"))
async def edit_profile_menu(message: Message):
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Cambiar nombre artístico", callback_data="edit_name")],
        [InlineKeyboardButton(text="📝 Cambiar descripción", callback_data="edit_description")],
        [InlineKeyboardButton(text="💰 Cambiar precio de suscripción", callback_data="edit_price")],
        [InlineKeyboardButton(text="📸 Cambiar foto de perfil", callback_data="edit_photo")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_edit")]
    ])
    
    await message.answer(
        "🔧 <b>EDITAR PERFIL</b>\n\n"
        "¿Qué deseas modificar en tu perfil?",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "edit_name")
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎨 <b>CAMBIAR NOMBRE ARTÍSTICO</b>\n\n"
        "Escribe tu nuevo nombre artístico:"
    )
    await state.set_state(ProfileEdit.waiting_for_new_name)

@router.message(ProfileEdit.waiting_for_new_name)
async def process_new_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer("❌ El nombre es muy largo. Máximo 50 caracteres. Inténtalo de nuevo:")
        return
    
    update_creator_display_name(message.from_user.id, message.text)
    
    await message.answer(
        f"✅ <b>Nombre artístico actualizado</b>\n\n"
        f"🎨 Nuevo nombre: {message.text}\n\n"
        f"Puedes ver tu perfil actualizado con /mi_perfil"
    )
    await state.clear()

@router.callback_query(F.data == "edit_description")
async def edit_description_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 <b>CAMBIAR DESCRIPCIÓN</b>\n\n"
        "Escribe tu nueva descripción (máximo 200 caracteres):"
    )
    await state.set_state(ProfileEdit.waiting_for_new_description)

@router.message(ProfileEdit.waiting_for_new_description)
async def process_new_description(message: Message, state: FSMContext):
    if len(message.text) > 200:
        await message.answer("❌ La descripción es muy larga. Máximo 200 caracteres. Inténtalo de nuevo:")
        return
    
    update_creator_description(message.from_user.id, message.text)
    
    await message.answer(
        f"✅ <b>Descripción actualizada</b>\n\n"
        f"📝 Nueva descripción: {message.text}\n\n"
        f"Puedes ver tu perfil actualizado con /mi_perfil"
    )
    await state.clear()

@router.callback_query(F.data == "edit_price")
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💰 <b>CAMBIAR PRECIO DE SUSCRIPCIÓN</b>\n\n"
        "Escribe el nuevo precio mensual en ⭐️ Stars:\n"
        "💡 Puedes poner 0 para suscripciones gratuitas\n"
        "Ejemplo: 150 (o 0 para gratis)"
    )
    await state.set_state(ProfileEdit.waiting_for_new_price)

@router.message(ProfileEdit.waiting_for_new_price)
async def process_new_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido (0 o mayor):")
        return
    
    update_creator_subscription_price(message.from_user.id, price)
    
    if price == 0:
        await message.answer(
            f"✅ <b>Precio de suscripción actualizado</b>\n\n"
            f"🆓 Nuevo precio: GRATIS (0 ⭐️)\n\n"
            f"Los nuevos suscriptores podrán suscribirse gratis.\n"
            f"Puedes ver tu perfil actualizado con /mi_perfil"
        )
    else:
        await message.answer(
            f"✅ <b>Precio de suscripción actualizado</b>\n\n"
            f"💰 Nuevo precio: {price} ⭐️\n\n"
            f"Los nuevos suscriptores pagarán este precio.\n"
            f"Puedes ver tu perfil actualizado con /mi_perfil"
        )
    await state.clear()

@router.callback_query(F.data == "edit_photo")
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📸 <b>CAMBIAR FOTO DE PERFIL</b>\n\n"
        "Envía tu nueva foto de perfil o escribe 'quitar' para eliminar la foto actual:"
    )
    await state.set_state(ProfileEdit.waiting_for_new_photo)

@router.message(ProfileEdit.waiting_for_new_photo)
async def process_new_photo(message: Message, state: FSMContext):
    photo_url = None
    
    if message.photo:
        photo_url = message.photo[-1].file_id
        update_creator_photo(message.from_user.id, photo_url)
        await message.answer(
            "✅ <b>Foto de perfil actualizada</b>\n\n"
            "📸 Tu nueva foto de perfil ha sido guardada.\n"
            "Puedes ver tu perfil actualizado con /mi_perfil"
        )
    elif message.text and message.text.lower() == 'quitar':
        update_creator_photo(message.from_user.id, None)
        await message.answer(
            "✅ <b>Foto de perfil eliminada</b>\n\n"
            "📸 Has eliminado tu foto de perfil.\n"
            "Puedes ver tu perfil actualizado con /mi_perfil"
        )
    else:
        await message.answer("❌ Por favor envía una imagen o escribe 'quitar':")
        return
    
    await state.clear()

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "❌ <b>Edición cancelada</b>\n\n"
        "No se realizaron cambios en tu perfil."
    )
    await state.clear()

async def show_my_catalog(message: Message, state: FSMContext):
    """Muestra el catálogo del creador para gestionar su contenido"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    # Obtener contenido PPV con estadísticas
    ppv_content = get_ppv_content_with_stats(message.from_user.id)
    
    if not ppv_content:
        await message.answer(
            "📚 <b>MI CATÁLOGO</b>\n\n"
            "😔 Aún no has creado ningún contenido PPV.\n\n"
            "💡 Usa /crear_contenido_ppv para empezar a crear contenido."
        )
        return
    
    # Mostrar lista de contenido con estadísticas
    text = "📚 <b>MI CATÁLOGO PPV</b>\n\n"
    text += f"📊 Total de contenidos: {len(ppv_content)}\n\n"
    
    keyboard = []
    
    for content in ppv_content[:10]:  # Mostrar máximo 10 por página
        content_id = content[0]
        title = content[2]
        description = content[3]
        price_stars = content[4]
        album_type = content[8] if len(content) > 8 else 'single'
        purchase_count = content[9] if len(content) > 9 else 0
        
        # Icono según tipo de contenido
        if album_type == 'album':
            icon = "📁"
            content_type = "Álbum"
        elif content[6] == "photo":
            icon = "📸"
            content_type = "Foto"
        else:
            icon = "🎥"
            content_type = "Video"
        
        # Limitar descripción
        short_desc = description[:30] + "..." if description and len(description) > 30 else (description or "Sin descripción")
        
        text += f"{icon} <b>{title}</b>\n"
        text += f"📝 {short_desc}\n"
        text += f"💰 Precio: {price_stars} ⭐️ | 🛒 Compras: {purchase_count}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Botón para gestionar este contenido
        keyboard.append([
            InlineKeyboardButton(
                text=f"{icon} Gestionar: {title[:20]}...", 
                callback_data=f"manage_content_{content_id}"
            )
        ])
    
    if len(ppv_content) > 10:
        text += f"💡 Mostrando los primeros 10 contenidos de {len(ppv_content)} totales"
    
    keyboard.append([InlineKeyboardButton(text="🔄 Actualizar", callback_data="refresh_catalog")])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup)
    await state.set_state(CatalogManagement.viewing_catalog)

@router.callback_query(F.data.startswith("manage_content_"))
async def manage_content(callback: CallbackQuery, state: FSMContext):
    """Gestiona un contenido específico"""
    await callback.answer()
    
    if is_user_banned(callback.from_user.id):
        await callback.message.edit_text("❌ Tu cuenta está baneada.")
        return
    
    content_id = int(callback.data.split("_")[2])
    
    # Obtener información del contenido
    content = get_ppv_content(content_id)
    if not content:
        await callback.message.edit_text("❌ Contenido no encontrado.")
        return
    
    # Verificar que sea el propietario
    if len(content) >= 9:
        content_id, creator_id, title, description, price_stars, file_id, file_type, created_at, album_type = content[:9]
    else:
        content_id, creator_id, title, description, price_stars, file_id, file_type = content[:7]
        album_type = 'single'
    
    if creator_id != callback.from_user.id:
        await callback.message.edit_text("❌ No tienes permisos para gestionar este contenido.")
        return
    
    # Obtener estadísticas de compras
    ppv_stats = get_ppv_content_with_stats(callback.from_user.id)
    purchase_count = 0
    for stat in ppv_stats:
        if stat[0] == content_id:
            purchase_count = stat[9] if len(stat) > 9 else 0
            break
    
    # Mostrar información detallada
    content_type = "📁 Álbum" if album_type == 'album' else ("📸 Foto" if file_type == "photo" else "🎥 Video")
    
    text = f"🔧 <b>GESTIONAR CONTENIDO</b>\n\n"
    text += f"{content_type}: <b>{title}</b>\n\n"
    text += f"📝 <b>Descripción:</b>\n{description or 'Sin descripción'}\n\n"
    text += f"💰 <b>Precio:</b> {price_stars} ⭐️\n"
    text += f"🛒 <b>Compras totales:</b> {purchase_count}\n"
    text += f"💎 <b>Ingresos generados:</b> {purchase_count * price_stars * 0.8:.0f} ⭐️\n\n"
    
    if album_type == 'album':
        album_items = get_ppv_album_items(content_id)
        text += f"📁 <b>Archivos en el álbum:</b> {len(album_items)}\n\n"
    
    text += f"📅 <b>Creado:</b> {created_at}\n"
    
    keyboard = [
        [InlineKeyboardButton(text="👁️ Ver contenido", callback_data=f"preview_content_{content_id}")],
        [InlineKeyboardButton(text="🗑️ Eliminar contenido", callback_data=f"delete_content_{content_id}")],
        [InlineKeyboardButton(text="📚 Volver al catálogo", callback_data="back_to_my_catalog")]
    ]
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(text, reply_markup=reply_markup)

@router.callback_query(F.data.startswith("preview_content_"))
async def preview_content(callback: CallbackQuery):
    """Muestra una vista previa del contenido"""
    await callback.answer()
    
    content_id = int(callback.data.split("_")[2])
    content = get_ppv_content(content_id)
    
    if not content:
        await callback.message.answer("❌ Contenido no encontrado.")
        return
    
    # Verificar que sea el propietario
    creator_id = content[1]
    if creator_id != callback.from_user.id:
        await callback.message.answer("❌ No tienes permisos para ver este contenido.")
        return
    
    title = content[2]
    description = content[3]
    file_id = content[5]
    file_type = content[6]
    album_type = content[8] if len(content) > 8 else 'single'
    
    caption = f"👁️ <b>Vista previa: {title}</b>\n\n📝 {description or 'Sin descripción'}"
    
    try:
        if album_type == 'album':
            # Mostrar álbum completo
            from aiogram.utils.media_group import MediaGroupBuilder
            album_items = get_ppv_album_items(content_id)
            
            if album_items:
                media_group = MediaGroupBuilder(caption=caption)
                
                for item in album_items:
                    item_file_id = item[2]
                    item_file_type = item[3]
                    
                    if item_file_type == "photo":
                        media_group.add_photo(media=item_file_id)
                    elif item_file_type == "video":
                        media_group.add_video(media=item_file_id)
                
                await callback.message.bot.send_media_group(
                    chat_id=callback.message.chat.id,
                    media=media_group.build()
                )
        else:
            # Contenido individual
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
        await callback.message.answer(f"❌ Error mostrando el contenido: {str(e)}")

@router.callback_query(F.data.startswith("delete_content_"))
async def confirm_delete_content(callback: CallbackQuery, state: FSMContext):
    """Confirma la eliminación de contenido"""
    await callback.answer()
    
    content_id = int(callback.data.split("_")[2])
    content = get_ppv_content(content_id)
    
    if not content:
        await callback.message.edit_text("❌ Contenido no encontrado.")
        return
    
    # Verificar que sea el propietario
    creator_id = content[1]
    if creator_id != callback.from_user.id:
        await callback.message.edit_text("❌ No tienes permisos para eliminar este contenido.")
        return
    
    title = content[2]
    album_type = content[8] if len(content) > 8 else 'single'
    
    # Obtener estadísticas de compras
    ppv_stats = get_ppv_content_with_stats(callback.from_user.id)
    purchase_count = 0
    for stat in ppv_stats:
        if stat[0] == content_id:
            purchase_count = stat[9] if len(stat) > 9 else 0
            break
    
    content_type = "📁 álbum" if album_type == 'album' else ("📸 foto" if content[6] == "photo" else "🎥 video")
    
    text = f"⚠️ <b>CONFIRMAR ELIMINACIÓN</b>\n\n"
    text += f"¿Estás seguro de que quieres eliminar este {content_type}?\n\n"
    text += f"📝 <b>Título:</b> {title}\n"
    text += f"🛒 <b>Compras realizadas:</b> {purchase_count}\n\n"
    
    if purchase_count > 0:
        text += f"⚠️ <b>ADVERTENCIA:</b> Este contenido ya fue comprado por {purchase_count} usuario(s). "
        text += f"Al eliminarlo, estos usuarios perderán acceso al contenido.\n\n"
    
    text += f"❌ <b>Esta acción NO se puede deshacer.</b>"
    
    keyboard = [
        [InlineKeyboardButton(text="✅ Sí, eliminar", callback_data=f"confirm_delete_{content_id}")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"manage_content_{content_id}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(text, reply_markup=reply_markup)
    await state.update_data(deleting_content_id=content_id)
    await state.set_state(CatalogManagement.confirming_deletion)

@router.callback_query(F.data.startswith("confirm_delete_"))
async def execute_delete_content(callback: CallbackQuery, state: FSMContext):
    """Ejecuta la eliminación del contenido"""
    await callback.answer()
    
    content_id = int(callback.data.split("_")[2])
    
    # Eliminar contenido de la base de datos
    success, message = delete_ppv_content(content_id, callback.from_user.id)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Contenido eliminado exitosamente</b>\n\n"
            f"🗑️ El contenido ha sido eliminado de tu catálogo.\n"
            f"💡 Los usuarios que ya lo compraron perderán acceso al mismo.\n\n"
            f"Usa /mi_catalogo para ver tu catálogo actualizado."
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Error al eliminar contenido</b>\n\n"
            f"📝 {message}\n\n"
            f"💡 Inténtalo de nuevo más tarde."
        )
    
    await state.clear()

@router.callback_query(F.data == "refresh_catalog")
async def refresh_catalog(callback: CallbackQuery, state: FSMContext):
    """Actualiza la vista del catálogo"""
    await callback.answer("🔄 Actualizando catálogo...")
    
    # Simular el comando /mi_catalogo
    message_mock = type('MockMessage', (), {
        'from_user': callback.from_user,
        'answer': callback.message.bot.send_message,
        'chat': callback.message.chat
    })()
    
    # Eliminar mensaje anterior
    await callback.message.delete()
    
    # Mostrar catálogo actualizado
    await show_my_catalog(message_mock, state)

@router.callback_query(F.data == "back_to_my_catalog")
async def back_to_my_catalog(callback: CallbackQuery, state: FSMContext):
    """Regresa al catálogo principal"""
    await callback.answer()
    
    # Simular el comando /mi_catalogo
    message_mock = type('MockMessage', (), {
        'from_user': callback.from_user,
        'answer': callback.message.edit_text,
        'chat': callback.message.chat
    })()
    
    await show_my_catalog(message_mock, state)

@router.message(Command("mi_catalogo"))
async def my_catalog_management(message: Message, state: FSMContext):
    """Gestión del catálogo del creador - versión para teclado"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        return
    
    # Obtener contenido PPV con estadísticas
    ppv_content = get_ppv_content_with_stats(message.from_user.id)
    
    if not ppv_content:
        await message.answer(
            "📊 <b>MI CATÁLOGO PPV</b>\n\n"
            "📝 Aún no has creado contenido PPV.\n\n"
            "💡 <b>¿Cómo empezar?</b>\n"
            "• Usa 📸 Crear PPV para subir tu primer contenido\n"
            "• Puedes crear fotos, videos o álbumes\n"
            "• Define precios personalizados en ⭐️ Stars\n\n"
            "🚀 ¡Comienza a monetizar tu contenido ahora!"
        )
        return
    
    # Mostrar resumen del catálogo
    total_content = len(ppv_content)
    total_sales = sum(item[9] if len(item) > 9 else 0 for item in ppv_content)  # purchase_count
    
    catalog_text = f"📊 <b>MI CATÁLOGO PPV</b>\n\n"
    catalog_text += f"📈 <b>Resumen:</b>\n"
    catalog_text += f"📦 Total contenidos: {total_content}\n"
    catalog_text += f"💰 Ventas totales: {total_sales}\n\n"
    catalog_text += f"📋 <b>Contenidos recientes:</b>\n\n"
    
    # Mostrar últimos 5 contenidos
    for i, content in enumerate(ppv_content[:5]):
        content_id = content[0]
        title = content[2]
        price_stars = content[4] 
        purchase_count = content[9] if len(content) > 9 else 0
        album_type = content[8] if len(content) > 8 else 'single'
        
        content_type = "📁 Álbum" if album_type == 'album' else "📸 Individual"
        catalog_text += f"{i+1}. {content_type} - {price_stars} ⭐️\n"
        catalog_text += f"   💰 Ventas: {purchase_count}\n"
        catalog_text += f"   🆔 ID: <code>{content_id}</code>\n\n"
    
    if total_content > 5:
        catalog_text += f"... y {total_content - 5} contenidos más\n\n"
    
    catalog_text += "💡 Para gestionar contenidos específicos, usa:\n"
    catalog_text += "• <code>/eliminar_ppv &lt;ID&gt;</code> - Eliminar contenido\n"
    catalog_text += "• 📸 Crear PPV - Subir nuevo contenido"
    
    await message.answer(catalog_text)

