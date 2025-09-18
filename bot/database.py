# bot/database.py
import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "platform.db")

def get_db_connection():
    """Get a database connection with foreign keys enabled"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS creators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            display_name TEXT,
            description TEXT,
            subscription_price INTEGER,
            photo_url TEXT,
            payout_method TEXT,
            balance_stars INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payer_id INTEGER,
            receiver_id INTEGER,
            amount_stars INTEGER,
            commission_stars INTEGER,
            type TEXT, -- 'subscription', 'ppv', 'tip'
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fan_id INTEGER,
            creator_id INTEGER,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ppv_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            title TEXT,
            description TEXT,
            price_stars INTEGER,
            file_id TEXT,
            file_type TEXT, -- 'photo' or 'video'
            album_type TEXT DEFAULT 'single', -- 'single' or 'album'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ppv_album_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER,
            file_id TEXT,
            file_type TEXT, -- 'photo' or 'video'
            order_position INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (album_id) REFERENCES ppv_content(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ppv_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            content_id INTEGER,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(buyer_id, content_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # === VIDEOCALL SYSTEM TABLES ===
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videocall_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER UNIQUE,
            price_10min INTEGER DEFAULT 0,
            price_30min INTEGER DEFAULT 0,
            price_60min INTEGER DEFAULT 0,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES creators(user_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videocall_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            creator_id INTEGER,
            fan_id INTEGER,
            duration_minutes INTEGER,
            price_stars INTEGER,
            group_id INTEGER,
            status TEXT DEFAULT 'pending', -- 'pending', 'active', 'completed', 'cancelled'
            payment_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES creators(user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videocall_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER UNIQUE,
            session_id TEXT,
            group_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES videocall_sessions(session_id) ON DELETE CASCADE
        )
    ''')
    
    # === MIGRATION LOGIC FOR EXISTING DATABASES ===
    # Add album_type column to ppv_content if it doesn't exist (for databases created before this feature)
    try:
        # Check if album_type column exists
        cursor.execute("PRAGMA table_info(ppv_content)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'album_type' not in columns:
            cursor.execute("ALTER TABLE ppv_content ADD COLUMN album_type TEXT DEFAULT 'single'")
            print("✅ Migration: Added album_type column to ppv_content table")
    except Exception as e:
        print(f"⚠️ Migration warning: {e}")
    
    conn.commit()
    conn.close()

def add_creator(user_id, username, display_name, description, subscription_price, photo_url, payout_method):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO creators 
        (user_id, username, display_name, description, subscription_price, photo_url, payout_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, display_name, description, subscription_price, photo_url, payout_method))
    conn.commit()
    conn.close()

def get_creator_by_id(creator_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM creators WHERE user_id = ?", (creator_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_transaction(payer_id, receiver_id, amount_stars, commission_stars, tx_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (payer_id, receiver_id, amount_stars, commission_stars, type)
        VALUES (?, ?, ?, ?, ?)
    ''', (payer_id, receiver_id, amount_stars, commission_stars, tx_type))
    conn.commit()
    conn.close()

def add_subscriber(fan_id, creator_id, expires_at):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO subscribers (fan_id, creator_id, expires_at)
        VALUES (?, ?, ?)
    ''', (fan_id, creator_id, expires_at))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance_stars FROM creators WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def update_balance(user_id, stars):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET balance_stars = balance_stars + ? WHERE user_id = ?", (stars, user_id))
    conn.commit()
    conn.close()

def update_creator_display_name(user_id, display_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET display_name = ? WHERE user_id = ?", (display_name, user_id))
    conn.commit()
    conn.close()

def update_creator_description(user_id, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET description = ? WHERE user_id = ?", (description, user_id))
    conn.commit()
    conn.close()

def update_creator_subscription_price(user_id, price):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET subscription_price = ? WHERE user_id = ?", (price, user_id))
    conn.commit()
    conn.close()

def update_creator_photo(user_id, photo_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET photo_url = ? WHERE user_id = ?", (photo_url, user_id))
    conn.commit()
    conn.close()

def get_all_creators():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM creators")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_available_creators(user_id):
    """Obtiene creadores disponibles (no suscritos) para un usuario específico"""
    import time
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener creadores excluyendo:
    # 1. Al propio usuario (no verse a sí mismo)
    # 2. Creadores a los que ya está suscrito activamente
    cursor.execute('''
        SELECT * FROM creators 
        WHERE user_id != ? 
        AND user_id NOT IN (
            SELECT creator_id FROM subscribers 
            WHERE fan_id = ? AND expires_at > ?
        )
        ORDER BY created_at DESC
    ''', (user_id, user_id, int(time.time())))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_creator_stats(creator_id):
    """Obtiene el número de suscriptores activos para un creador"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Usar DATETIME para comparar fechas correctamente
        cursor.execute("""
            SELECT COUNT(*) FROM subscribers 
            WHERE creator_id = ? 
            AND datetime(expires_at, 'unixepoch') > datetime('now')
        """, (creator_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        # Asegurar que devuelve siempre un entero
        if result and result[0] is not None:
            return int(result[0])
        else:
            return 0
            
    except Exception as e:
        # Si hay error, devolver 0 como fallback
        print(f"❌ Error en get_creator_stats: {e}")
        return 0

def is_user_banned(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def ban_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_ppv_content(creator_id, title, description, price_stars, file_id=None, file_type=None, album_type='single'):
    """Crea contenido PPV individual o álbum"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ppv_content (creator_id, title, description, price_stars, file_id, file_type, album_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (creator_id, title, description, price_stars, file_id, file_type, album_type))
    content_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return content_id

def add_ppv_album_item(album_id, file_id, file_type, order_position):
    """Agrega un archivo al álbum PPV"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ppv_album_items (album_id, file_id, file_type, order_position)
        VALUES (?, ?, ?, ?)
    ''', (album_id, file_id, file_type, order_position))
    conn.commit()
    conn.close()

def get_ppv_album_items(album_id):
    """Obtiene todos los archivos de un álbum en orden"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ppv_album_items 
        WHERE album_id = ? 
        ORDER BY order_position
    ''', (album_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_ppv_content(content_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ppv_content WHERE id = ?", (content_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_ppv_purchase(buyer_id, content_id):
    """Agrega una compra PPV de manera segura, evitando duplicados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO ppv_purchases (buyer_id, content_id) VALUES (?, ?)", (buyer_id, content_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Ya existe esta compra, no hacer nada
        return False
    finally:
        conn.close()

def has_purchased_ppv(buyer_id, content_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM ppv_purchases WHERE buyer_id = ? AND content_id = ?", (buyer_id, content_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_admin_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM creators")
    total_creators = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(commission_stars) FROM transactions")
    total_commission = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_creators, total_transactions, total_commission

def withdraw_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET balance_stars = balance_stars - ? WHERE user_id = ? AND balance_stars >= ?", (amount, user_id, amount))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

import time

def get_active_subscriptions(user_id):
    """Obtiene las suscripciones activas de un usuario"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM subscribers 
        WHERE fan_id = ? AND expires_at > ?
    ''', (user_id, int(time.time())))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_ppv_by_creator(creator_id):
    """Obtiene todo el contenido PPV de un creador específico ordenado del más antiguo al más reciente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ppv_content 
        WHERE creator_id = ?
        ORDER BY created_at ASC, id ASC
    ''', (creator_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_ppv_content(content_id, creator_id):
    """Elimina contenido PPV y todos sus elementos de álbum asociados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar que el contenido pertenece al creador
        cursor.execute("SELECT creator_id FROM ppv_content WHERE id = ?", (content_id,))
        result = cursor.fetchone()
        
        if not result or result[0] != creator_id:
            return False, "Contenido no encontrado o no tienes permisos para eliminarlo"
        
        # Eliminar elementos del álbum si los hay (la FK con CASCADE se encarga de esto)
        cursor.execute("DELETE FROM ppv_album_items WHERE album_id = ?", (content_id,))
        
        # Eliminar compras asociadas
        cursor.execute("DELETE FROM ppv_purchases WHERE content_id = ?", (content_id,))
        
        # Eliminar el contenido principal
        cursor.execute("DELETE FROM ppv_content WHERE id = ?", (content_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            return True, "Contenido eliminado exitosamente"
        else:
            return False, "No se pudo eliminar el contenido"
            
    except Exception as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        conn.close()

def get_ppv_content_with_stats(creator_id):
    """Obtiene contenido PPV con estadísticas de compras"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            p.*,
            COUNT(pp.id) as purchase_count,
            COALESCE(COUNT(pp.id) * p.price_stars, 0) as total_sales
        FROM ppv_content p
        LEFT JOIN ppv_purchases pp ON p.id = pp.content_id
        WHERE p.creator_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (creator_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# === VIDEOCALL SYSTEM FUNCTIONS ===

def set_videocall_settings(creator_id, price_10min, price_30min, price_60min, enabled=True):
    """Configura los precios de videollamadas para un creador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO videocall_settings 
        (creator_id, price_10min, price_30min, price_60min, enabled, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (creator_id, price_10min, price_30min, price_60min, enabled))
    conn.commit()
    conn.close()

def get_videocall_settings(creator_id):
    """Obtiene la configuración de videollamadas de un creador"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videocall_settings WHERE creator_id = ?", (creator_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def create_videocall_session(session_id, creator_id, fan_id, duration_minutes, price_stars, payment_verified=False):
    """Crea una nueva sesión de videollamada"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videocall_sessions 
        (session_id, creator_id, fan_id, duration_minutes, price_stars, status, payment_verified)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
    ''', (session_id, creator_id, fan_id, duration_minutes, price_stars, payment_verified))
    conn.commit()
    conn.close()

def verify_videocall_payment(session_id):
    """Marca el pago de una videollamada como verificado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE videocall_sessions 
        SET payment_verified = 1
        WHERE session_id = ?
    ''', (session_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def get_videocall_session(session_id):
    """Obtiene información de una sesión de videollamada"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videocall_sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_videocall_session_status(session_id, status, group_id=None):
    """Actualiza el estado de una sesión de videollamada"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if group_id:
        cursor.execute('''
            UPDATE videocall_sessions 
            SET status = ?, group_id = ?, started_at = CURRENT_TIMESTAMP 
            WHERE session_id = ?
        ''', (status, group_id, session_id))
    else:
        cursor.execute('''
            UPDATE videocall_sessions 
            SET status = ?, ended_at = CURRENT_TIMESTAMP 
            WHERE session_id = ?
        ''', (status, session_id))
    conn.commit()
    conn.close()

def create_videocall_group(group_id, session_id, group_title):
    """Registra un grupo de videollamada creado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videocall_groups (group_id, session_id, group_title)
        VALUES (?, ?, ?)
    ''', (group_id, session_id, group_title))
    conn.commit()
    conn.close()

def delete_videocall_group(group_id):
    """Marca un grupo de videollamada como eliminado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE videocall_groups 
        SET deleted_at = CURRENT_TIMESTAMP 
        WHERE group_id = ?
    ''', (group_id,))
    conn.commit()
    conn.close()

def get_active_videocall_sessions(creator_id=None, fan_id=None):
    """Obtiene sesiones activas de videollamadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if creator_id:
        cursor.execute('''
            SELECT * FROM videocall_sessions 
            WHERE creator_id = ? AND status IN ('pending', 'active')
            ORDER BY created_at DESC
        ''', (creator_id,))
    elif fan_id:
        cursor.execute('''
            SELECT * FROM videocall_sessions 
            WHERE fan_id = ? AND status IN ('pending', 'active')
            ORDER BY created_at DESC
        ''', (fan_id,))
    else:
        cursor.execute('''
            SELECT * FROM videocall_sessions 
            WHERE status IN ('pending', 'active')
            ORDER BY created_at DESC
        ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

