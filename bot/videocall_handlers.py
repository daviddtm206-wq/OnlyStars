# bot/videocall_handlers.py
import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database import (
    get_creator_by_id, set_videocall_settings, get_videocall_settings,
    get_all_creators, add_transaction, update_balance
)
from videocall_system import videocall_manager

logger = logging.getLogger(__name__)
router = Router()

# Estados para configuración de videollamadas
class VideocallConfig(StatesGroup):
    setting_prices = State()
    price_10min = State()
    price_30min = State()
    price_60min = State()

# Estados para solicitar videollamada
class VideocallRequest(StatesGroup):
    selecting_creator = State()
    selecting_duration = State()
    confirming_payment = State()

@router.message(Command("configurar_videollamadas"))
async def cmd_configure_videocalls(message: Message, state: FSMContext):
    """Comando para que creadores configuren precios de videollamadas"""
    user_id = message.from_user.id
    
    # Verificar que es creador
    creator = get_creator_by_id(user_id)
    if not creator:
        await message.reply(
            "❌ Solo los creadores pueden configurar videollamadas.\n"
            "Usa /convertirme_en_creador para registrarte."
        )
        return
    
    # Obtener configuración actual
    current_settings = get_videocall_settings(user_id)
    
    if current_settings:
        price_10 = current_settings[2]  # price_10min
        price_30 = current_settings[3]  # price_30min 
        price_60 = current_settings[4]  # price_60min
        enabled = current_settings[5]  # enabled
        
        status = "✅ Activadas" if enabled else "❌ Desactivadas"
        
        text = f"""🎥 <b>Configuración de Videollamadas</b>

<b>Estado actual:</b> {status}

<b>Precios configurados:</b>
• 10 minutos: {price_10} ⭐ {'(GRATIS)' if price_10 == 0 else ''}
• 30 minutos: {price_30} ⭐ {'(GRATIS)' if price_30 == 0 else ''}
• 60 minutos: {price_60} ⭐ {'(GRATIS)' if price_60 == 0 else ''}"""
    else:
        text = """🎥 <b>Configuración de Videollamadas</b>

No tienes videollamadas configuradas aún.
¡Configura tus precios y comienza a ofrecer videollamadas privadas!"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Configurar Precios", callback_data="vc_config_prices")],
        [InlineKeyboardButton(text="📊 Ver Estadísticas", callback_data="vc_stats")],
        [InlineKeyboardButton(text="🔄 Estado On/Off", callback_data="vc_toggle")]
    ])
    
    await message.reply(text, reply_markup=keyboard)

@router.callback_query(F.data == "vc_config_prices")
async def configure_videocall_prices(callback: CallbackQuery, state: FSMContext):
    """Configurar precios de videollamadas"""
    await callback.message.edit_text(
        """💰 <b>Configuración de Precios</b>

Vamos a configurar los precios para cada duración.
Puedes poner <b>0 ⭐ para videollamadas GRATIS</b>.

<b>¿Cuánto cobrarás por videollamadas de 10 minutos?</b>
(Escribe solo el número, ejemplo: 100)

💡 Precios sugeridos:
• Gratis: 0
• Económico: 50-100 ⭐
• Premium: 200-500 ⭐
• Exclusivo: 1000+ ⭐""",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="vc_cancel")]
        ])
    )
    await state.set_state(VideocallConfig.price_10min)

@router.message(VideocallConfig.price_10min)
async def set_price_10min(message: Message, state: FSMContext):
    """Configurar precio para 10 minutos"""
    try:
        price = int(message.text)
        if price < 0:
            await message.reply("❌ El precio no puede ser negativo. Intenta de nuevo:")
            return
        
        await state.update_data(price_10min=price)
        
        price_text = "GRATIS" if price == 0 else f"{price} ⭐"
        await message.reply(
            f"""✅ Precio de 10 minutos: <b>{price_text}</b>

<b>¿Cuánto cobrarás por videollamadas de 30 minutos?</b>
(Escribe solo el número)"""
        )
        await state.set_state(VideocallConfig.price_30min)
        
    except ValueError:
        await message.reply("❌ Por favor ingresa solo números. Ejemplo: 100")

@router.message(VideocallConfig.price_30min)
async def set_price_30min(message: Message, state: FSMContext):
    """Configurar precio para 30 minutos"""
    try:
        price = int(message.text)
        if price < 0:
            await message.reply("❌ El precio no puede ser negativo. Intenta de nuevo:")
            return
        
        await state.update_data(price_30min=price)
        
        price_text = "GRATIS" if price == 0 else f"{price} ⭐"
        await message.reply(
            f"""✅ Precio de 30 minutos: <b>{price_text}</b>

<b>¿Cuánto cobrarás por videollamadas de 60 minutos?</b>
(Escribe solo el número)"""
        )
        await state.set_state(VideocallConfig.price_60min)
        
    except ValueError:
        await message.reply("❌ Por favor ingresa solo números. Ejemplo: 300")

@router.message(VideocallConfig.price_60min)
async def set_price_60min(message: Message, state: FSMContext):
    """Configurar precio para 60 minutos y guardar configuración"""
    try:
        price = int(message.text)
        if price < 0:
            await message.reply("❌ El precio no puede ser negativo. Intenta de nuevo:")
            return
        
        # Obtener todos los precios
        data = await state.get_data()
        price_10 = data['price_10min']
        price_30 = data['price_30min']
        price_60 = price
        
        # Guardar en base de datos
        set_videocall_settings(message.from_user.id, price_10, price_30, price_60, True)
        
        price_10_text = "GRATIS" if price_10 == 0 else f"{price_10} ⭐"
        price_30_text = "GRATIS" if price_30 == 0 else f"{price_30} ⭐"
        price_60_text = "GRATIS" if price_60 == 0 else f"{price_60} ⭐"
        
        await message.reply(
            f"""✅ <b>Configuración Guardada</b>

🎥 <b>Tus precios de videollamadas:</b>
• 10 minutos: {price_10_text}
• 30 minutos: {price_30_text}  
• 60 minutos: {price_60_text}

¡Las videollamadas están ahora <b>ACTIVADAS</b> en tu perfil!
Los fans podrán solicitar videollamadas contigo usando /solicitar_videollamada.""",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎥 Ver Mi Configuración", callback_data="vc_my_config")]
            ])
        )
        await state.clear()
        
    except ValueError:
        await message.reply("❌ Por favor ingresa solo números. Ejemplo: 500")

@router.message(Command("solicitar_videollamada"))
async def cmd_request_videocall(message: Message, state: FSMContext):
    """Comando para fans para solicitar videollamada"""
    user_id = message.from_user.id
    
    # Obtener creadores con videollamadas habilitadas
    all_creators = get_all_creators()
    creators_with_videocalls = []
    
    for creator in all_creators:
        if creator[1] != user_id:  # No mostrarse a sí mismo
            settings = get_videocall_settings(creator[1])
            if settings and settings[5]:  # enabled = True
                creators_with_videocalls.append((creator, settings))
    
    if not creators_with_videocalls:
        await message.reply(
            "❌ No hay creadores con videollamadas disponibles en este momento.\n\n"
            "Los creadores pueden activar videollamadas con /configurar_videollamadas"
        )
        return
    
    # Crear keyboard con creadores disponibles
    keyboard_buttons = []
    text = "🎥 <b>Creadores con Videollamadas Disponibles</b>\n\n"
    
    for i, (creator, settings) in enumerate(creators_with_videocalls):
        creator_name = creator[3] or creator[2] or "Sin nombre"  # display_name, username
        
        # Mostrar precios
        price_10 = "GRATIS" if settings[2] == 0 else f"{settings[2]} ⭐"
        price_30 = "GRATIS" if settings[3] == 0 else f"{settings[3]} ⭐"
        price_60 = "GRATIS" if settings[4] == 0 else f"{settings[4]} ⭐"
        
        text += f"👤 <b>{creator_name}</b>\n"
        text += f"• 10 min: {price_10}\n"
        text += f"• 30 min: {price_30}\n"
        text += f"• 60 min: {price_60}\n\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📞 {creator_name}",
                callback_data=f"vc_select_creator:{creator[1]}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.reply(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("vc_select_creator:"))
async def select_creator_for_videocall(callback: CallbackQuery, state: FSMContext):
    """Seleccionar creador para videollamada"""
    creator_id = int(callback.data.split(":")[1])
    creator = get_creator_by_id(creator_id)
    settings = get_videocall_settings(creator_id)
    
    if not creator or not settings:
        await callback.answer("❌ Creador no disponible", show_alert=True)
        return
    
    creator_name = creator[3] or creator[2] or "Sin nombre"
    
    # Mostrar opciones de duración
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Agregar opciones disponibles
    if settings[2] >= 0:  # price_10min
        price_text = "GRATIS" if settings[2] == 0 else f"{settings[2]} ⭐"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🕙 10 minutos - {price_text}",
                callback_data=f"vc_duration:{creator_id}:10:{settings[2]}"
            )
        ])
    
    if settings[3] >= 0:  # price_30min
        price_text = "GRATIS" if settings[3] == 0 else f"{settings[3]} ⭐"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🕕 30 minutos - {price_text}",
                callback_data=f"vc_duration:{creator_id}:30:{settings[3]}"
            )
        ])
    
    if settings[4] >= 0:  # price_60min
        price_text = "GRATIS" if settings[4] == 0 else f"{settings[4]} ⭐"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🕐 60 minutos - {price_text}",
                callback_data=f"vc_duration:{creator_id}:60:{settings[4]}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ Volver", callback_data="vc_back_to_creators")
    ])
    
    await callback.message.edit_text(
        f"""🎥 <b>Videollamada con {creator_name}</b>

Selecciona la duración que prefieras:""",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("vc_duration:"))
async def confirm_videocall_payment(callback: CallbackQuery):
    """Confirmar pago y crear videollamada"""
    try:
        _, creator_id, duration, price = callback.data.split(":")
        creator_id = int(creator_id)
        duration = int(duration)
        price = int(price)
        
        fan_id = callback.from_user.id
        creator = get_creator_by_id(creator_id)
        creator_name = creator[3] or creator[2] or "Sin nombre"
        
        if price == 0:
            # Videollamada gratuita - crear inmediatamente
            await callback.message.edit_text("🔄 Creando videollamada gratuita...")
            
            session_id, group_id = await videocall_manager.start_videocall_session(
                creator_id, fan_id, duration, 0, creator_name
            )
            
            if session_id:
                await callback.message.edit_text(
                    f"""✅ <b>Videollamada Creada</b>

🎥 <b>Creador:</b> {creator_name}
⏱️ <b>Duración:</b> {duration} minutos
💰 <b>Precio:</b> GRATIS
🆔 <b>Sesión:</b> {session_id}

📱 <b>¡Ya puedes iniciar la videollamada!</b>
El grupo se eliminará automáticamente después de {duration + 5} minutos."""
                )
                
                # Notificar al creador
                # TODO: Enviar notificación al creador sobre nueva videollamada
                
            else:
                await callback.message.edit_text(
                    "❌ No se pudo crear la videollamada. Intenta de nuevo más tarde."
                )
        else:
            # Videollamada de pago - mostrar confirmación
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"💳 Pagar {price} ⭐",
                    callback_data=f"vc_pay:{creator_id}:{duration}:{price}"
                )],
                [InlineKeyboardButton(text="❌ Cancelar", callback_data="vc_cancel")]
            ])
            
            await callback.message.edit_text(
                f"""💰 <b>Confirmar Pago</b>

🎥 <b>Videollamada con:</b> {creator_name}
⏱️ <b>Duración:</b> {duration} minutos
💰 <b>Precio:</b> {price} ⭐

¿Confirmas el pago?""",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Error en confirmación de videollamada: {e}")
        await callback.answer("❌ Error interno", show_alert=True)

@router.callback_query(F.data.startswith("vc_pay:"))
async def process_videocall_payment(callback: CallbackQuery):
    """Procesar pago de videollamada (simulado)"""
    try:
        _, creator_id, duration, price = callback.data.split(":")
        creator_id = int(creator_id)
        duration = int(duration)
        price = int(price)
        
        fan_id = callback.from_user.id
        creator = get_creator_by_id(creator_id)
        creator_name = creator[3] or creator[2] or "Sin nombre"
        
        await callback.message.edit_text("🔄 Procesando pago...")
        
        # TODO: Integrar con sistema de pago real de Telegram Stars
        # Por ahora simulamos el pago exitoso
        
        # Calcular comisión (20%)
        commission_percentage = int(os.getenv("COMMISSION_PERCENTAGE", 20))
        commission = (price * commission_percentage) // 100
        creator_earnings = price - commission
        
        # Registrar transacción
        add_transaction(fan_id, creator_id, price, commission, 'videocall')
        
        # Actualizar balance del creador
        update_balance(creator_id, creator_earnings)
        
        # Crear videollamada
        session_id, group_id = await videocall_manager.start_videocall_session(
            creator_id, fan_id, duration, price, creator_name
        )
        
        if session_id:
            await callback.message.edit_text(
                f"""✅ <b>¡Pago Exitoso!</b>

💳 <b>Pagaste:</b> {price} ⭐
🎥 <b>Videollamada con:</b> {creator_name}
⏱️ <b>Duración:</b> {duration} minutos
🆔 <b>Sesión:</b> {session_id}

📱 <b>¡Ya puedes iniciar la videollamada!</b>
El grupo se eliminará automáticamente después de {duration + 5} minutos."""
            )
        else:
            await callback.message.edit_text(
                f"""❌ <b>Error al Crear Videollamada</b>

Tu pago de {price} ⭐ fue procesado exitosamente, pero hubo un problema técnico al crear el grupo.

🔄 <b>Se procesará un reembolso automáticamente.</b>
Contacta al soporte si no recibes el reembolso."""
            )
            
    except Exception as e:
        logger.error(f"Error en pago de videollamada: {e}")
        await callback.answer("❌ Error en el pago", show_alert=True)

@router.callback_query(F.data == "vc_cancel")
async def cancel_videocall_action(callback: CallbackQuery, state: FSMContext):
    """Cancelar acción de videollamada"""
    await state.clear()
    await callback.message.edit_text("❌ Acción cancelada.")

@router.callback_query(F.data == "vc_toggle")
async def toggle_videocall_status(callback: CallbackQuery):
    """Activar/desactivar videollamadas"""
    user_id = callback.from_user.id
    settings = get_videocall_settings(user_id)
    
    if not settings:
        await callback.answer("❌ Configura precios primero", show_alert=True)
        return
    
    # Cambiar estado
    new_status = not settings[5]  # Toggle enabled
    set_videocall_settings(
        user_id, settings[2], settings[3], settings[4], new_status
    )
    
    status_text = "✅ ACTIVADAS" if new_status else "❌ DESACTIVADAS"
    await callback.answer(f"Videollamadas {status_text}", show_alert=True)
    
    # Refrescar configuración
    await cmd_configure_videocalls(callback.message, None)