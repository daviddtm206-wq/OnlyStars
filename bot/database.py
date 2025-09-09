# bot/database.py
import sqlite3
import os

DB_PATH = "platform.db"

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
