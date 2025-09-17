# bot/creator_handlers_fixed.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (add_creator, get_creator_by_id, get_all_creators, get_available_creators, get_creator_stats, 
                     get_user_balance, withdraw_balance, add_ppv_content, is_user_banned,
                     update_creator_display_name, update_creator_description, 
                     update_creator_subscription_price, update_creator_photo,
                     add_ppv_album_item, add_subscriber)
from dotenv import load_dotenv
from keyboards import get_creator_card_keyboard, get_subscription_confirmation_keyboard
import os
import time

load_dotenv()

router = Router()

async def show_creator_card(message: Message, creators: list, page: int = 0):
    """Muestra una tarjeta profesional de creador individual"""
    if page >= len(creators) or page < 0:
        await message.answer("❌ No hay más creadores para mostrar.")
        return
    
    creator = creators[page]
    user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance, created_at = creator[1:10]
    
    # Formatear el texto de la tarjeta de creador
    card_text = f"✨ <b>{display_name}</b>\n\n"
    card_text += f"📝 <i>{description}</i>\n\n"
    
    if subscription_price == 0:
        card_text += "🆓 <b>Suscripción GRATIS</b> ⭐️\n\n"
    else:
        card_text += f"💎 <b>Suscripción: {subscription_price} ⭐️</b>\n\n"
    
    card_text += f"👤 @{username if username else 'Usuario sin nombre'}\n"
    card_text += f"🆔 ID: {user_id}\n\n"
    card_text += "🌟 <i>¡Únete para acceder a contenido exclusivo!</i>"
    
    # Crear teclado inline con botones
    keyboard = get_creator_card_keyboard(user_id, page, len(creators))
    
    try:
        # Si hay foto de perfil, enviarla con el mensaje
        if photo_url:
            await message.answer_photo(
                photo=photo_url,
                caption=card_text,
                reply_markup=keyboard
            )
        else:
            # Si no hay foto, enviar solo el texto
            await message.answer(
                text=card_text,
                reply_markup=keyboard
            )
    except Exception as e:
        # Si falla cargar la foto, enviar solo texto
        await message.answer(
            text=card_text,
            reply_markup=keyboard
        )

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

class WithdrawalFlow(StatesGroup):
    waiting_for_amount = State()
    confirming_withdrawal = State()

class CreatePPVContent(StatesGroup):
    waiting_for_content = State()
    waiting_for_more_content = State()
    waiting_for_price = State()
    waiting_for_description = State()

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
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres. Inténtalo de nuevo:")
        return
    if len(name) > 50:
        await message.answer("❌ El nombre es muy largo (máximo 50 caracteres). Inténtalo de nuevo:")
        return
        
    await state.update_data(display_name=name)
    
    from keyboards import get_creator_name_confirmation_keyboard
    await message.answer(
        f"📝 <b>CONFIRMA TU NOMBRE ARTÍSTICO</b>\n\n"
        f"Nombre elegido: <b>{name}</b>\n\n"
        f"¿Es correcto este nombre? Será como te verán tus fans.",
        reply_markup=get_creator_name_confirmation_keyboard()
    )

@router.message(CreatorRegistration.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if len(description) > 200:
        await message.answer("❌ La descripción es muy larga. Máximo 200 caracteres. Inténtalo de nuevo:")
        return
    if len(description) < 10:
        await message.answer("❌ La descripción es muy corta. Mínimo 10 caracteres. Inténtalo de nuevo:")
        return
    
    await state.update_data(description=description)
    
    from keyboards import get_creator_description_confirmation_keyboard
    await message.answer(
        f"📝 <b>CONFIRMA TU DESCRIPCIÓN</b>\n\n"
        f"Descripción: <i>{description}</i>\n\n"
        f"¿Te gusta cómo se ve? Esto aparecerá en tu perfil público.",
        reply_markup=get_creator_description_confirmation_keyboard()
    )

# El proceso de precio ahora se maneja con callbacks en lugar de mensaje directo
# Esta función se mantiene para compatibilidad con precios personalizados
@router.message(CreatorRegistration.waiting_for_price)
async def process_custom_price(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        if price < 0:
            raise ValueError
        if price > 10000:
            await message.answer("❌ El precio máximo es 10,000 ⭐️. Inténtalo de nuevo:")
            return
    except ValueError:
        await message.answer("❌ Por favor ingresa un número válido (0 o mayor):")
        return
    
    await state.update_data(subscription_price=price)
    
    from keyboards import get_creator_photo_keyboard
    price_text = "GRATIS" if price == 0 else f"{price} ⭐️"
    await message.answer(
        f"✅ <b>PRECIO CONFIGURADO</b>\n\n"
        f"Precio de suscripción: <b>{price_text}</b>\n\n"
        f"📸 <b>Paso 4 de 5: FOTO DE PERFIL</b>\n"
        f"Sube una foto para que tus fans te conozcan mejor.",
        reply_markup=get_creator_photo_keyboard()
    )
    await state.set_state(CreatorRegistration.waiting_for_photo)

# El manejo de foto ahora se hace principalmente con callbacks
# Esta función maneja la subida directa de fotos
@router.message(CreatorRegistration.waiting_for_photo)
async def process_photo_upload(message: Message, state: FSMContext):
    if message.photo:
        photo_url = message.photo[-1].file_id
        await state.update_data(photo_url=photo_url)
        
        from keyboards import get_creator_payout_keyboard
        await message.answer(
            f"✅ <b>FOTO GUARDADA</b>\n\n"
            f"📸 Tu foto de perfil se ha guardado correctamente.\n\n"
            f"💳 <b>Paso 5 de 5: MÉTODO DE PAGO</b>\n"
            f"¿Cómo quieres recibir tus ganancias?",
            reply_markup=get_creator_payout_keyboard()
        )
        await state.set_state(CreatorRegistration.waiting_for_payout)
    else:
        await message.answer(
            "❌ Por favor envía una imagen válida o usa los botones del menú para saltar este paso."
        )

# ==================== CALLBACKS PARA REGISTRO CON BOTONES ====================

@router.callback_query(F.data == "confirm_name")
async def confirm_creator_name(callback: CallbackQuery, state: FSMContext):
    """Confirmar nombre artístico y continuar al siguiente paso"""
    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Paso 2 de 5: DESCRIPCIÓN</b>\n\n"
        "Escribe una descripción de ti y tu contenido.\n\n"
        "💡 <i>Ejemplo: 'Artista digital especializada en fanart de anime. Contenido exclusivo y tutoriales creativos.'</i>\n\n"
        "Máximo 200 caracteres:"
    )
    await state.set_state(CreatorRegistration.waiting_for_description)

@router.callback_query(F.data == "edit_name")
async def edit_creator_name(callback: CallbackQuery, state: FSMContext):
    """Volver a pedir el nombre artístico"""
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>Paso 1 de 5: NOMBRE ARTÍSTICO</b>\n\n"
        "Escribe un nuevo nombre artístico:\n\n"
        "💡 <i>Piensa en algo fácil de recordar y profesional</i>"
    )
    await state.set_state(CreatorRegistration.waiting_for_name)

@router.callback_query(F.data == "confirm_description")
async def confirm_creator_description(callback: CallbackQuery, state: FSMContext):
    """Confirmar descripción y mostrar selección de precios"""
    await callback.answer()
    
    from keyboards import get_creator_price_keyboard
    await callback.message.edit_text(
        "💰 <b>Paso 3 de 5: PRECIO DE SUSCRIPCIÓN</b>\n\n"
        "Elige el precio de tu suscripción mensual:\n\n"
        "🆓 <b>GRATIS:</b> Perfecto para empezar y conseguir fans\n"
        "⭐️ <b>50-200:</b> Precio moderado, bueno para la mayoría\n"
        "⭐️ <b>500-1000:</b> Contenido premium de alta calidad\n\n"
        "💡 <i>Puedes cambiar el precio más tarde</i>",
        reply_markup=get_creator_price_keyboard()
    )

@router.callback_query(F.data == "edit_description")
async def edit_creator_description(callback: CallbackQuery, state: FSMContext):
    """Volver a pedir la descripción"""
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>Paso 2 de 5: DESCRIPCIÓN</b>\n\n"
        "Escribe una nueva descripción (máximo 200 caracteres):\n\n"
        "💡 <i>Describe tu contenido de forma atractiva</i>"
    )
    await state.set_state(CreatorRegistration.waiting_for_description)

@router.callback_query(F.data.startswith("price_"))
async def select_subscription_price(callback: CallbackQuery, state: FSMContext):
    """Seleccionar precio de suscripción predefinido"""
    await callback.answer()
    
    price = int(callback.data.split("_")[1])
    await state.update_data(subscription_price=price)
    
    from keyboards import get_creator_photo_keyboard
    price_text = "GRATIS" if price == 0 else f"{price} ⭐️"
    
    await callback.message.edit_text(
        f"✅ <b>PRECIO SELECCIONADO</b>\n\n"
        f"Precio de suscripción: <b>{price_text}</b>\n\n"
        f"📸 <b>Paso 4 de 5: FOTO DE PERFIL</b>\n"
        f"Una foto atractiva aumenta hasta 3x más suscriptores.\n\n"
        f"¿Quieres subir una foto ahora?",
        reply_markup=get_creator_photo_keyboard()
    )
    await state.set_state(CreatorRegistration.waiting_for_photo)

@router.callback_query(F.data == "custom_price")
async def request_custom_price(callback: CallbackQuery, state: FSMContext):
    """Pedir precio personalizado"""
    await callback.answer()
    await callback.message.edit_text(
        "✏️ <b>PRECIO PERSONALIZADO</b>\n\n"
        "Escribe el precio de tu suscripción mensual en ⭐️ Stars:\n\n"
        "💡 <b>Ejemplos:</b>\n"
        "• 0 = Gratis\n"
        "• 150 = 150 ⭐️ (aprox $2 USD)\n"
        "• 750 = 750 ⭐️ (aprox $10 USD)\n\n"
        "<i>Escribe solo el número:</i>"
    )
    await state.set_state(CreatorRegistration.waiting_for_price)

@router.callback_query(F.data == "upload_photo_now")
async def request_photo_upload(callback: CallbackQuery, state: FSMContext):
    """Pedir subida de foto"""
    await callback.answer()
    await callback.message.edit_text(
        "📸 <b>SUBIR FOTO DE PERFIL</b>\n\n"
        "Envía tu mejor foto de perfil ahora.\n\n"
        "💡 <b>Consejos:</b>\n"
        "• Usa buena iluminación\n"
        "• Sonríe y mira a la cámara\n"
        "• Evita fotos borrosas\n\n"
        "<i>Envía la imagen ahora:</i>"
    )
    # Estado se mantiene en waiting_for_photo

@router.callback_query(F.data == "skip_photo")
async def skip_profile_photo(callback: CallbackQuery, state: FSMContext):
    """Saltar foto de perfil"""
    await callback.answer()
    await state.update_data(photo_url=None)
    
    from keyboards import get_creator_payout_keyboard
    await callback.message.edit_text(
        "⏭️ <b>FOTO OMITIDA</b>\n\n"
        "Puedes agregar una foto más tarde desde tu perfil.\n\n"
        "💳 <b>Paso 5 de 5: MÉTODO DE PAGO</b>\n"
        "¿Cómo prefieres recibir tus ganancias?",
        reply_markup=get_creator_payout_keyboard()
    )
    await state.set_state(CreatorRegistration.waiting_for_payout)

@router.callback_query(F.data == "cancel_registration")
async def cancel_creator_registration(callback: CallbackQuery, state: FSMContext):
    """Cancelar proceso de registro"""
    await callback.answer()
    await state.clear()
    
    from nav_states import NavigationManager, MenuState
    await NavigationManager.reset_to_main(state)
    
    from keyboards import get_main_keyboard
    await callback.message.edit_text(
        "❌ <b>REGISTRO CANCELADO</b>\n\n"
        "Has cancelado el registro de creador.\n"
        "Puedes intentarlo de nuevo cuando quieras usando el menú principal."
    )
    # Enviar nuevo mensaje con el menú principal
    await callback.message.answer(
        "🏠 <b>MENÚ PRINCIPAL</b>\n\n¿Qué te gustaría hacer?",
        reply_markup=get_main_keyboard(callback.from_user.id, callback.from_user.username)
    )

@router.callback_query(F.data == "payout_stars")
async def process_payout_method(callback: CallbackQuery, state: FSMContext):
    # Solo manejamos Stars ahora
    await state.update_data(payout_method="Stars")
    
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
            f"✅ ¡Bienvenido al panel de creador!"
        )
        
        # Mostrar el teclado completo de creador después del registro exitoso
        from keyboards import get_main_keyboard
        creator_keyboard = get_main_keyboard(callback.from_user.id, callback.from_user.username)
        
        await callback.message.answer(
            f"🎨 <b>PANEL DE CREADOR ACTIVADO</b>\n\n"
            f"¡Hola {data['display_name']}! Tu cuenta de creador está lista.\n\n"
            f"🚀 <b>¿Qué puedes hacer ahora?</b>\n"
            f"• 👤 Ver y editar tu perfil\n"
            f"• 📸 Crear contenido PPV premium\n"
            f"• 💰 Gestionar tus ganancias\n"
            f"• 📊 Administrar tu catálogo\n"
            f"• 🔍 Explorar otros creadores\n"
            f"• 👥 Ver la plataforma como fan\n\n"
            f"💡 <i>Usa los botones del menú para navegar por todas las opciones.</i>",
            reply_markup=creator_keyboard
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
    
    # 🎯 NUEVA LÓGICA: Solo mostrar creadores NO suscritos
    creators = get_available_creators(message.from_user.id)
    
    if not creators:
        await message.answer(
            "🎉 <b>¡FELICIDADES!</b>\n\n"
            "✅ Ya estás suscrito a todos los creadores disponibles\n"
            "📝 O no hay más creadores registrados en la plataforma.\n\n"
            "💡 <i>Vuelve más tarde para descubrir nuevos creadores.</i>"
        )
        return
    
    # Mostrar el primer creador disponible en formato de tarjeta
    await show_creator_card(message, creators, 0)

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
    
    # Extraer datos del creador por índice específico para evitar confusiones
    user_id = creator[1]           # user_id  
    username = creator[2]          # username
    display_name = creator[3]      # display_name
    description = creator[4]       # description  
    subscription_price = creator[5] # subscription_price
    photo_url = creator[6]         # photo_url
    payout_method = creator[7]     # payout_method
    balance_stars = creator[8]     # balance_stars
    created_at = creator[9]        # created_at
    
    # Obtener número de suscriptores activos
    subscribers_count = get_creator_stats(message.from_user.id)
        
    balance_usd = balance_stars * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = f"👤 <b>TU PERFIL DE CREADOR</b>\n\n"
    text += f"🎨 Nombre artístico: {display_name}\n"
    text += f"📝 Descripción: {description}\n"
    text += f"💰 Precio suscripción: {subscription_price} ⭐️\n"
    text += f"👥 Suscriptores activos: {subscribers_count}\n"
    text += f"💎 Balance: {balance_stars} ⭐️ (${balance_usd:.2f})\n"
    text += f"💳 Método de retiro: {payout_method}\n\n"
    text += f"💡 <i>Usa los botones del menú para acceder a todas las funciones disponibles.</i>"
    
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

# ==================== CALLBACKS PARA TARJETAS DE CREADORES ====================

@router.callback_query(F.data.startswith("subscribe_"))
async def handle_subscribe_button(callback: CallbackQuery):
    """Maneja el botón de suscribirse a un creador"""
    creator_id = int(callback.data.split("_")[1])
    
    creator = get_creator_by_id(creator_id)
    if not creator:
        await callback.answer("❌ Creador no encontrado.", show_alert=True)
        return
    
    user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance, created_at = creator[1:10]
    
    if subscription_price == 0:
        # Suscripción gratuita - suscribir directamente
        try:
            expires_at = int(time.time()) + (30 * 24 * 60 * 60)  # 30 días
            add_subscriber(callback.from_user.id, creator_id, expires_at)
            
            # Borrar mensaje anterior y enviar uno nuevo
            await callback.message.delete()
            await callback.message.answer(
                f"🎉 <b>¡Suscripción exitosa!</b>\n\n"
                f"✨ Te has suscrito GRATIS a <b>{display_name}</b>\n"
                f"📅 Tu suscripción es válida por 30 días\n\n"
                f"🎨 Ahora tienes acceso a su contenido exclusivo en 📺 Mis Catálogos"
            )
            await callback.answer("🎉 ¡Suscripción gratuita activada!", show_alert=True)
        except Exception as e:
            await callback.answer("❌ Error al procesar la suscripción.", show_alert=True)
    else:
        # Suscripción de pago - mostrar confirmación
        keyboard = get_subscription_confirmation_keyboard(creator_id, subscription_price)
        
        # Borrar mensaje anterior y enviar uno nuevo
        await callback.message.delete()
        await callback.message.answer(
            f"💎 <b>Confirmar Suscripción</b>\n\n"
            f"✨ Creador: <b>{display_name}</b>\n"
            f"💰 Precio: <b>{subscription_price} ⭐️</b>\n"
            f"📅 Duración: <b>30 días</b>\n\n"
            f"🎨 Tendrás acceso a todo su contenido exclusivo\n\n"
            f"¿Confirmas tu suscripción?",
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("confirm_sub_"))
async def handle_confirm_subscription(callback: CallbackQuery):
    """Confirma la suscripción de pago usando Telegram Stars"""
    creator_id = int(callback.data.split("_")[2])
    
    creator = get_creator_by_id(creator_id)
    if not creator:
        await callback.answer("❌ Creador no encontrado.", show_alert=True)
        return
    
    user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance, created_at = creator[1:10]
    
    # Aquí deberías integrar el sistema de pagos con Telegram Stars
    # Por ahora simularemos una suscripción exitosa
    try:
        expires_at = int(time.time()) + (30 * 24 * 60 * 60)  # 30 días
        add_subscriber(callback.from_user.id, creator_id, expires_at)
        
        await callback.message.edit_text(
            f"🎉 <b>¡Pago procesado con éxito!</b>\n\n"
            f"✨ Te has suscrito a <b>{display_name}</b>\n"
            f"💰 Costo: {subscription_price} ⭐️\n"
            f"📅 Tu suscripción es válida por 30 días\n\n"
            f"🎨 Ahora tienes acceso a su contenido exclusivo en 📺 Mis Catálogos"
        )
        await callback.answer("💫 ¡Suscripción activada!", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Error al procesar el pago.", show_alert=True)

@router.callback_query(F.data == "cancel_subscription")
async def handle_cancel_subscription(callback: CallbackQuery):
    """Cancela el proceso de suscripción"""
    await callback.message.edit_text(
        "❌ <b>Suscripción cancelada</b>\n\n"
        "Puedes explorar otros creadores cuando gustes usando /explorar_creadores"
    )
    await callback.answer("Operación cancelada")


@router.callback_query(F.data.startswith("creator_next_"))
async def handle_next_creator(callback: CallbackQuery):
    """Navega al siguiente creador"""
    current_page = int(callback.data.split("_")[2])
    # 🎯 NUEVA LÓGICA: Solo mostrar creadores NO suscritos
    creators = get_available_creators(callback.from_user.id)
    
    next_page = current_page + 1
    if next_page < len(creators):
        await show_creator_card_callback(callback, creators, next_page)
    else:
        await callback.answer("❌ No hay más creadores disponibles.", show_alert=True)

@router.callback_query(F.data.startswith("creator_prev_"))
async def handle_prev_creator(callback: CallbackQuery):
    """Navega al creador anterior"""
    current_page = int(callback.data.split("_")[2])
    # 🎯 NUEVA LÓGICA: Solo mostrar creadores NO suscritos
    creators = get_available_creators(callback.from_user.id)
    
    prev_page = current_page - 1
    if prev_page >= 0:
        await show_creator_card_callback(callback, creators, prev_page)
    else:
        await callback.answer("❌ No hay creadores anteriores.", show_alert=True)

@router.callback_query(F.data == "back_to_explore")
async def handle_back_to_explore(callback: CallbackQuery):
    """Regresa a la exploración de creadores"""
    # 🎯 NUEVA LÓGICA: Solo mostrar creadores NO suscritos
    creators = get_available_creators(callback.from_user.id)
    if creators:
        await show_creator_card_callback(callback, creators, 0)
    else:
        await callback.message.edit_text(
            "🎉 <b>¡EXCELENTE!</b>\n\n"
            "✅ Ya estás suscrito a todos los creadores disponibles.\n\n"
            "💡 <i>Vuelve más tarde para descubrir nuevos creadores.</i>"
        )

async def show_creator_card_callback(callback: CallbackQuery, creators: list, page: int = 0):
    """Muestra una tarjeta de creador en un callback (para navegación)"""
    if page >= len(creators) or page < 0:
        await callback.answer("❌ No hay más creadores para mostrar.", show_alert=True)
        return
    
    creator = creators[page]
    user_id, username, display_name, description, subscription_price, photo_url, payout_method, balance, created_at = creator[1:10]
    
    # Formatear el texto de la tarjeta de creador
    card_text = f"✨ <b>{display_name}</b>\n\n"
    card_text += f"📝 <i>{description}</i>\n\n"
    
    if subscription_price == 0:
        card_text += "🆓 <b>Suscripción GRATIS</b> ⭐️\n\n"
    else:
        card_text += f"💎 <b>Suscripción: {subscription_price} ⭐️</b>\n\n"
    
    card_text += f"👤 @{username if username else 'Usuario sin nombre'}\n"
    card_text += f"🆔 ID: {user_id}\n\n"
    card_text += "🌟 <i>¡Únete para acceder a contenido exclusivo!</i>"
    
    # Crear teclado inline con botones
    keyboard = get_creator_card_keyboard(user_id, page, len(creators))
    
    try:
        # Borrar mensaje anterior y enviar uno nuevo
        await callback.message.delete()
        
        # Si hay foto de perfil, enviarla con el mensaje
        if photo_url:
            await callback.message.answer_photo(
                photo=photo_url,
                caption=card_text,
                reply_markup=keyboard
            )
        else:
            # Si no hay foto, enviar solo el texto
            await callback.message.answer(
                text=card_text,
                reply_markup=keyboard
            )
        await callback.answer()
    except Exception as e:
        await callback.answer("❌ Error al cargar creador.", show_alert=True)

# ==================== WITHDRAWAL FLOW HANDLERS ====================

@router.message(WithdrawalFlow.waiting_for_amount)
async def process_withdrawal_amount(message: Message, state: FSMContext):
    """Procesar cantidad para retiro"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        await state.clear()
        return
    
    creator = get_creator_by_id(message.from_user.id)
    if not creator:
        await message.answer("❌ No estás registrado como creador.")
        await state.clear()
        return
    
    amount_text = message.text.strip().lower()
    current_balance = get_user_balance(message.from_user.id)
    min_withdrawal = int(os.getenv("MIN_WITHDRAWAL", 1000))
    
    # Manejar "todo" para retirar todo el balance
    if amount_text == "todo":
        if current_balance < min_withdrawal:
            await message.answer(
                f"❌ <b>No puedes retirar todo</b>\n\n"
                f"Tu balance actual ({current_balance} ⭐️) está por debajo del mínimo de retiro ({min_withdrawal} ⭐️)."
            )
            return
        amount = current_balance
    else:
        try:
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "❌ <b>Cantidad inválida</b>\n\n"
                "Por favor ingresa un número válido o escribe 'todo' para retirar todo tu balance.\n\n"
                "<i>Ejemplo: 1000</i>"
            )
            return
    
    # Validaciones
    if amount < min_withdrawal:
        await message.answer(f"❌ El retiro mínimo es de {min_withdrawal} ⭐️")
        return
    
    if amount > current_balance:
        await message.answer(
            f"❌ <b>Balance insuficiente</b>\n\n"
            f"Cantidad solicitada: {amount} ⭐️\n"
            f"Tu balance actual: {current_balance} ⭐️"
        )
        return
    
    # Mostrar confirmación
    amount_usd = amount * float(os.getenv("EXCHANGE_RATE", 0.013))
    remaining_balance = current_balance - amount
    
    confirmation_text = (
        f"💸 <b>CONFIRMAR RETIRO</b>\n\n"
        f"💰 <b>Cantidad a retirar:</b> {amount} ⭐️\n"
        f"💵 <b>Equivalente USD:</b> ~${amount_usd:.2f}\n"
        f"💎 <b>Balance restante:</b> {remaining_balance} ⭐️\n\n"
        f"🏦 <b>Método de pago:</b> {creator[6]}\n"
        f"🕰️ <b>Tiempo de procesamiento:</b> 24-48 horas\n\n"
        f"❗️ <b>¿Confirmas este retiro?</b>"
    )
    
    from keyboards import get_withdrawal_confirmation_keyboard
    await message.answer(
        text=confirmation_text,
        reply_markup=get_withdrawal_confirmation_keyboard(amount)
    )
    await state.update_data(withdrawal_amount=amount)
    await state.set_state(WithdrawalFlow.confirming_withdrawal)

@router.callback_query(F.data.startswith("confirm_withdraw_"))
async def confirm_withdrawal(callback: CallbackQuery, state: FSMContext):
    """Confirmar y procesar retiro"""
    if is_user_banned(callback.from_user.id):
        await callback.answer("❌ Tu cuenta está baneada.", show_alert=True)
        await state.clear()
        return
    
    creator = get_creator_by_id(callback.from_user.id)
    if not creator:
        await callback.answer("❌ No se encontró tu perfil de creador.", show_alert=True)
        await state.clear()
        return
    
    amount = int(callback.data.split("_")[2])
    current_balance = get_user_balance(callback.from_user.id)
    
    # Verificación final de balance (por si cambió entre confirmación)
    if amount > current_balance:
        await callback.message.edit_text(
            f"❌ <b>Error: Balance insuficiente</b>\n\n"
            f"Tu balance actual: {current_balance} ⭐️\n"
            f"El retiro ha sido cancelado."
        )
        await state.clear()
        await callback.answer()
        return
    
    # Procesar retiro
    if withdraw_balance(callback.from_user.id, amount):
        amount_usd = amount * float(os.getenv("EXCHANGE_RATE", 0.013))
        remaining_balance = current_balance - amount
        
        success_text = (
            f"✅ <b>RETIRO PROCESADO EXITOSAMENTE</b>\n\n"
            f"💰 <b>Monto retirado:</b> {amount} ⭐️\n"
            f"💵 <b>Equivalente USD:</b> ~${amount_usd:.2f}\n"
            f"💎 <b>Balance restante:</b> {remaining_balance} ⭐️\n\n"
            f"🏦 <b>El dinero será transferido según tu método de pago configurado.</b>\n"
            f"🕰️ <b>Tiempo estimado:</b> 24-48 horas\n\n"
            f"📞 <b>Recibirás una notificación cuando se complete.</b>"
        )
        
        await callback.message.edit_text(
            text=success_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Ver Balance Actualizado", callback_data="profile_balance")],
                [InlineKeyboardButton(text="🔙 Volver al Panel", callback_data="back_to_creator_main")]
            ])
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Error al procesar retiro</b>\n\n"
            f"Hubo un problema técnico. Inténtalo de nuevo más tarde.\n\n"
            f"Si el problema persiste, contacta al soporte."
        )
    
    await state.clear()
    await callback.answer()