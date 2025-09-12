# bot/database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "platform.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ppv_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            content_id INTEGER,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banned_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_creator(user_id, username, display_name, description, subscription_price, photo_url, payout_method):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO creators 
        (user_id, username, display_name, description, subscription_price, photo_url, payout_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, display_name, description, subscription_price, photo_url, payout_method))
    conn.commit()
    conn.close()

def get_creator_by_id(creator_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM creators WHERE user_id = ?", (creator_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_transaction(payer_id, receiver_id, amount_stars, commission_stars, tx_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (payer_id, receiver_id, amount_stars, commission_stars, type)
        VALUES (?, ?, ?, ?, ?)
    ''', (payer_id, receiver_id, amount_stars, commission_stars, tx_type))
    conn.commit()
    conn.close()

def add_subscriber(fan_id, creator_id, expires_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO subscribers (fan_id, creator_id, expires_at)
        VALUES (?, ?, ?)
    ''', (fan_id, creator_id, expires_at))
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT balance_stars FROM creators WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def update_balance(user_id, stars):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET balance_stars = balance_stars + ? WHERE user_id = ?", (stars, user_id))
    conn.commit()
    conn.close()

def update_creator_display_name(user_id, display_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET display_name = ? WHERE user_id = ?", (display_name, user_id))
    conn.commit()
    conn.close()

def update_creator_description(user_id, description):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET description = ? WHERE user_id = ?", (description, user_id))
    conn.commit()
    conn.close()

def update_creator_subscription_price(user_id, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET subscription_price = ? WHERE user_id = ?", (price, user_id))
    conn.commit()
    conn.close()

def update_creator_photo(user_id, photo_url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET photo_url = ? WHERE user_id = ?", (photo_url, user_id))
    conn.commit()
    conn.close()

def get_all_creators():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM creators")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_creator_stats(creator_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE creator_id = ? AND expires_at > ?", (creator_id, int(time.time())))
    subscribers_count = cursor.fetchone()[0]
    conn.close()
    return subscribers_count

def is_user_banned(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_ppv_content(creator_id, title, description, price_stars, file_id, file_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ppv_content (creator_id, title, description, price_stars, file_id, file_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (creator_id, title, description, price_stars, file_id, file_type))
    content_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return content_id

def get_ppv_content(content_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ppv_content WHERE id = ?", (content_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_ppv_purchase(buyer_id, content_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ppv_purchases (buyer_id, content_id) VALUES (?, ?)", (buyer_id, content_id))
    conn.commit()
    conn.close()

def has_purchased_ppv(buyer_id, content_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM ppv_purchases WHERE buyer_id = ? AND content_id = ?", (buyer_id, content_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_admin_stats():
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE creators SET balance_stars = balance_stars - ? WHERE user_id = ? AND balance_stars >= ?", (amount, user_id, amount))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

import time

def get_active_subscriptions(user_id):
    """Obtiene las suscripciones activas de un usuario"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM subscribers 
        WHERE fan_id = ? AND expires_at > ?
    ''', (user_id, int(time.time())))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_ppv_by_creator(creator_id):
    """Obtiene todo el contenido PPV de un creador específico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM ppv_content 
        WHERE creator_id = ?
        ORDER BY created_at DESC
    ''', (creator_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
