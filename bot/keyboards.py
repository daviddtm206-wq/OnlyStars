# bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_creator_by_id
import os
from dotenv import load_dotenv

load_dotenv()

def get_main_keyboard(user_id: int, username: str = None) -> ReplyKeyboardMarkup:
    """Genera el teclado principal según el rol del usuario"""
    creator = get_creator_by_id(user_id)
    admin_username = os.getenv("ADMIN_USERNAME", "@admin")
    
    # Función para verificar si es admin por username
    def is_admin_user(check_username: str) -> bool:
        if not check_username:
            return False
        user_at = f"@{check_username}" if not check_username.startswith("@") else check_username
        return user_at == admin_username or check_username == admin_username.replace("@", "")
    
    if creator:
        # Teclado para creadores registrados
        keyboard = [
            [
                KeyboardButton(text="👤 Mi Perfil"),
                KeyboardButton(text="💎 Balance")
            ],
            [
                KeyboardButton(text="📸 Crear PPV"),
                KeyboardButton(text="📊 Mi Catálogo")
            ],
            [
                KeyboardButton(text="⚙️ Editar Perfil"),
                KeyboardButton(text="🔍 Explorar")
            ],
            [
                KeyboardButton(text="ℹ️ Ayuda"),
                KeyboardButton(text="👥 Ver Como Fan")
            ]
        ]
        
        # Si es admin, agregar botón de panel admin
        if is_admin_user(creator[2]):
            keyboard.insert(-1, [KeyboardButton(text="🛡️ Admin Panel")])
            
    else:
        # Teclado para usuarios/fans
        keyboard = [
            [
                KeyboardButton(text="🔍 Explorar Creadores"),
                KeyboardButton(text="📺 Mis Catálogos")
            ],
            [
                KeyboardButton(text="🎨 Ser Creador"),
                KeyboardButton(text="💰 Enviar Propina")
            ],
            [
                KeyboardButton(text="🛒 Comprar PPV"),
                KeyboardButton(text="ℹ️ Ayuda")
            ]
        ]
        
        # Agregar botón de admin si el usuario es administrador (sin necesidad de ser creador)
        if username and is_admin_user(username):
            keyboard.insert(-1, [KeyboardButton(text="🛡️ Admin Panel")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True,
        one_time_keyboard=False
    )

def get_fan_keyboard() -> ReplyKeyboardMarkup:
    """Teclado simplificado para vista de fan"""
    keyboard = [
        [
            KeyboardButton(text="🔍 Explorar Creadores"),
            KeyboardButton(text="📺 Mis Catálogos")
        ],
        [
            KeyboardButton(text="💰 Enviar Propina"),
            KeyboardButton(text="🛒 Comprar PPV")
        ],
        [
            KeyboardButton(text="ℹ️ Ayuda"),
            KeyboardButton(text="🎨 Volver a Creador")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True,
        one_time_keyboard=False
    )

def get_registration_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para confirmación de registro"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Confirmar Registro", callback_data="confirm_registration")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_registration")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_balance_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para opciones de balance"""
    keyboard = [
        [InlineKeyboardButton(text="💰 Retirar Ganancias", callback_data="withdraw_menu")],
        [InlineKeyboardButton(text="📊 Ver Historial", callback_data="view_history")],
        [InlineKeyboardButton(text="🔄 Actualizar Balance", callback_data="refresh_balance")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_creator_profile_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para perfil de creador"""
    keyboard = [
        [
            InlineKeyboardButton(text="⚙️ Editar Perfil", callback_data="edit_profile_menu"),
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="view_stats")
        ],
        [
            InlineKeyboardButton(text="💰 Ver Balance", callback_data="check_balance"),
            InlineKeyboardButton(text="📸 Crear PPV", callback_data="create_ppv")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ppv_creation_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para creación de PPV"""
    keyboard = [
        [InlineKeyboardButton(text="📸 Subir Foto", callback_data="upload_photo")],
        [InlineKeyboardButton(text="🎥 Subir Video", callback_data="upload_video")],
        [InlineKeyboardButton(text="📁 Crear Álbum", callback_data="create_album")],
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="cancel_ppv")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_price_selection_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para selección rápida de precios"""
    keyboard = [
        [
            InlineKeyboardButton(text="💎 50 ⭐️", callback_data="price_50"),
            InlineKeyboardButton(text="💎 100 ⭐️", callback_data="price_100"),
            InlineKeyboardButton(text="💎 200 ⭐️", callback_data="price_200")
        ],
        [
            InlineKeyboardButton(text="💎 500 ⭐️", callback_data="price_500"),
            InlineKeyboardButton(text="💎 1000 ⭐️", callback_data="price_1000"),
            InlineKeyboardButton(text="✏️ Precio Personalizado", callback_data="custom_price")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Teclado inline para panel de administrador"""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Estadísticas", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Usuarios", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="💰 Comisiones", callback_data="admin_commissions"),
            InlineKeyboardButton(text="🚫 Gestión de Baneos", callback_data="admin_bans")
        ],
        [
            InlineKeyboardButton(text="📢 Anuncio Global", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🔧 Configuración", callback_data="admin_config")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
