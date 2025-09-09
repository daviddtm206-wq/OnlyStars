# bot/admin_handlers.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_admin_stats, ban_user, is_user_banned
from dotenv import load_dotenv
import os

load_dotenv()

router = Router()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@Daviddtm")

def is_admin(user):
    return f"@{user.username}" == ADMIN_USERNAME or user.username == ADMIN_USERNAME.replace("@", "")

@router.message(Command("admin_panel"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    total_creators, total_transactions, total_commission = get_admin_stats()
    commission_usd = total_commission * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = f"👑 <b>PANEL DE ADMINISTRADOR</b>\n\n"
    text += f"📊 <b>Estadísticas de la plataforma:</b>\n"
    text += f"👥 Total de creadores: {total_creators}\n"
    text += f"💳 Total de transacciones: {total_transactions}\n"
    text += f"💰 Comisión acumulada: {total_commission} ⭐️\n"
    text += f"💵 Comisión en USD: ${commission_usd:.2f}\n\n"
    text += f"🔧 <b>Comandos disponibles:</b>\n"
    text += f"• <code>/banear_usuario &lt;ID&gt;</code> - Banear usuario\n"
    text += f"• <code>/stats</code> - Ver estadísticas detalladas"
    
    await message.answer(text)

@router.message(Command("banear_usuario"))
async def ban_user_command(message: Message):
    if not is_admin(message.from_user):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Uso: /banear_usuario &lt;ID_de_usuario&gt;\nEjemplo: /banear_usuario 123456789")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ El ID de usuario debe ser un número válido.")
        return
    
    if is_user_banned(user_id):
        await message.answer(f"⚠️ El usuario {user_id} ya está baneado.")
        return
    
    ban_user(user_id)
    await message.answer(f"✅ Usuario {user_id} ha sido baneado exitosamente.")

@router.message(Command("stats"))
async def detailed_stats(message: Message):
    if not is_admin(message.from_user):
        await message.answer("❌ No tienes permisos de administrador.")
        return
    
    total_creators, total_transactions, total_commission = get_admin_stats()
    commission_usd = total_commission * float(os.getenv("EXCHANGE_RATE", 0.013))
    
    text = f"📈 <b>ESTADÍSTICAS DETALLADAS</b>\n\n"
    text += f"👥 Creadores registrados: {total_creators}\n"
    text += f"💳 Transacciones totales: {total_transactions}\n"
    text += f"⭐️ Comisión total: {total_commission} Stars\n"
    text += f"💵 Comisión en USD: ${commission_usd:.2f}\n"
    text += f"📊 Comisión por transacción: {os.getenv('COMMISSION_PERCENTAGE', 20)}%\n"
    text += f"💎 Tasa de cambio: ${os.getenv('EXCHANGE_RATE', 0.013)} por Star"
    
    await message.answer(text)