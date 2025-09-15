# bot/admin_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import (get_admin_stats, ban_user, is_user_banned, get_creator_by_id, 
                     get_all_creators)
from keyboards import get_admin_keyboard
from dotenv import load_dotenv
import os

load_dotenv()

router = Router()

def is_admin(user_id: int, username: str) -> bool:
    """Verifica si el usuario es administrador"""
    admin_username = os.getenv("ADMIN_USERNAME", "@admin")
    if username:
        user_username = f"@{username}" if not username.startswith("@") else username
        return user_username == admin_username
    return False

@router.message(Command("admin_panel"))
async def admin_panel(message: Message):
    """Panel de administrador principal"""
    if is_user_banned(message.from_user.id):
        await message.answer("❌ Tu cuenta está baneada.")
        return
    
    # Verificar permisos de administrador
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.answer(
            "❌ <b>Acceso denegado</b>\n\n"
            "No tienes permisos de administrador para acceder a este panel."
        )
        return
    
    # Obtener estadísticas
    total_creators, total_transactions, total_commission = get_admin_stats()
    
    text = (
        "🛡️ <b>PANEL DE ADMINISTRADOR</b>\n\n"
        f"📊 <b>Estadísticas de la plataforma:</b>\n"
        f"👥 Total creadores: {total_creators}\n"
        f"💰 Total transacciones: {total_transactions}\n"
        f"💎 Comisiones ganadas: {total_commission} ⭐️\n\n"
        f"🔧 <b>Herramientas disponibles:</b>"
    )
    
    keyboard = get_admin_keyboard()
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Mostrar estadísticas detalladas"""
    if not is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer("❌ Sin permisos de administrador", show_alert=True)
        return
    
    total_creators, total_transactions, total_commission = get_admin_stats()
    commission_usd = total_commission * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = (
        "📊 <b>ESTADÍSTICAS DETALLADAS</b>\n\n"
        f"👥 <b>Creadores registrados:</b> {total_creators}\n"
        f"💰 <b>Transacciones totales:</b> {total_transactions}\n"
        f"💎 <b>Comisiones ganadas:</b> {total_commission} ⭐️\n"
        f"💵 <b>Equivalente en USD:</b> ${commission_usd:.2f}\n\n"
        f"📈 <b>Comisión por plataforma:</b> 20%\n"
        f"⭐️ <b>Powered by Telegram Stars</b>"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_users")
async def show_admin_users(callback: CallbackQuery):
    """Gestionar usuarios"""
    if not is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer("❌ Sin permisos de administrador", show_alert=True)
        return
    
    creators = get_all_creators()
    
    text = "👥 <b>GESTIÓN DE USUARIOS</b>\n\n"
    if creators:
        text += f"📋 <b>Creadores registrados ({len(creators)}):</b>\n\n"
        for creator in creators[:10]:  # Mostrar solo los primeros 10
            user_id, username, display_name, _, _, _, _, _, _ = creator[1:10]
            banned_status = "🚫 BANEADO" if is_user_banned(user_id) else "✅ Activo"
            text += f"👤 {display_name} (@{username})\n"
            text += f"🆔 ID: <code>{user_id}</code>\n"
            text += f"📊 Estado: {banned_status}\n\n"
        
        if len(creators) > 10:
            text += f"... y {len(creators) - 10} más\n\n"
    else:
        text += "😔 No hay creadores registrados\n\n"
    
    text += (
        "🔧 <b>Comandos de administrador:</b>\n"
        "• <code>/banear_usuario [user_id]</code> - Banear usuario\n"
        "• <code>/stats</code> - Estadísticas completas"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_commissions")
async def show_admin_commissions(callback: CallbackQuery):
    """Mostrar información de comisiones"""
    if not is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer("❌ Sin permisos de administrador", show_alert=True)
        return
    
    total_creators, total_transactions, total_commission = get_admin_stats()
    commission_rate = int(os.getenv("COMMISSION_PERCENTAGE", 20))
    commission_usd = total_commission * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = (
        "💰 <b>GESTIÓN DE COMISIONES</b>\n\n"
        f"📊 <b>Configuración actual:</b>\n"
        f"💎 Tasa de comisión: {commission_rate}%\n"
        f"⭐️ Moneda: Telegram Stars (XTR)\n"
        f"💱 Tasa de cambio: ${os.getenv('EXCHANGE_RATE', 0.013)} por Star\n\n"
        f"📈 <b>Ingresos acumulados:</b>\n"
        f"⭐️ Total en Stars: {total_commission}\n"
        f"💵 Equivalente USD: ${commission_usd:.2f}\n\n"
        f"📋 <b>Transacciones procesadas:</b> {total_transactions}\n"
        f"👥 <b>Creadores activos:</b> {total_creators}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_bans")
async def show_admin_bans(callback: CallbackQuery):
    """Gestionar baneos"""
    if not is_admin(callback.from_user.id, callback.from_user.username):
        await callback.answer("❌ Sin permisos de administrador", show_alert=True)
        return
    
    text = (
        "🚫 <b>GESTIÓN DE BANEOS</b>\n\n"
        "🔧 <b>Comandos disponibles:</b>\n"
        "• <code>/banear_usuario [user_id]</code>\n"
        "  Banea a un usuario por ID\n\n"
        "• <code>/admin_panel</code>\n"
        "  Volver al panel principal\n\n"
        "⚠️ <b>Nota:</b> Los usuarios baneados no pueden:\n"
        "• Registrarse como creadores\n"
        "• Hacer compras o suscripciones\n"
        "• Enviar propinas\n"
        "• Usar comandos del bot"
    )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

@router.message(Command("banear_usuario"))
async def ban_user_command(message: Message):
    """Comando para banear usuarios"""
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ <b>Uso incorrecto</b>\n\n"
            "Usa: <code>/banear_usuario [user_id]</code>\n"
            "Ejemplo: <code>/banear_usuario 123456789</code>"
        )
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ El ID de usuario debe ser un número válido.")
        return
    
    # Verificar que no se banee a sí mismo
    if user_id == message.from_user.id:
        await message.answer("❌ No puedes banearte a ti mismo.")
        return
    
    # Banear usuario
    ban_user(user_id)
    
    await message.answer(
        f"✅ <b>Usuario baneado exitosamente</b>\n\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"🚫 El usuario ya no puede usar el bot.\n\n"
        f"🔧 Usa /admin_panel para gestionar más usuarios."
    )

@router.message(Command("stats"))
async def admin_stats_command(message: Message):
    """Comando de estadísticas detalladas"""
    if not is_admin(message.from_user.id, message.from_user.username):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    total_creators, total_transactions, total_commission = get_admin_stats()
    commission_usd = total_commission * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = (
        "📊 <b>ESTADÍSTICAS COMPLETAS DE LA PLATAFORMA</b>\n\n"
        f"👥 <b>Creadores registrados:</b> {total_creators}\n"
        f"💰 <b>Transacciones procesadas:</b> {total_transactions}\n"
        f"💎 <b>Comisiones generadas:</b> {total_commission} ⭐️\n"
        f"💵 <b>Valor en USD:</b> ${commission_usd:.2f}\n\n"
        f"⚙️ <b>Configuración:</b>\n"
        f"• Comisión por plataforma: {os.getenv('COMMISSION_PERCENTAGE', 20)}%\n"
        f"• Retiro mínimo: {os.getenv('MIN_WITHDRAWAL', 1000)} ⭐️\n"
        f"• Tasa de cambio: ${os.getenv('EXCHANGE_RATE', 0.013)}/Star\n\n"
        f"🚀 <b>OnlyStars Bot - Administrador: {os.getenv('ADMIN_USERNAME')}</b>"
    )
    
    await message.answer(text)