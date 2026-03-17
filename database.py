import sqlite3

import os

# store database in workspace root so every module sees the same file regardless
# of current working directory (Streamlit may change cwd when running pages).
DB_NAME = os.path.join(os.path.dirname(__file__), "app.db")

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ---------------- USERS TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        failed_attempts INTEGER DEFAULT 0,
        is_locked INTEGER DEFAULT 0,
        created_at TEXT ,
        last_login TEXT
    )
    """)
    # make sure email/username comparisons are effectively case-insensitive by
    # adding indexes on the lowered values; this doesn't change existing data
    # but helps the application enforce uniqueness at SQL level in case the
    # table was created earlier without proper normalization.
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_lower_email ON users(LOWER(email))"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_lower_username ON users(LOWER(username))"
    )

    # ---------------- TRANSACTIONS TABLE ----------------
    # This table tracks payments/orders for downloads or other transactions.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_id TEXT,
        payment_id TEXT,
        amount INTEGER,
        status TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    # ---------------- IMAGE HISTORY TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS image_history (
        image_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        original_image_path TEXT,
        processed_image_path TEXT,
        style_applied TEXT,
        processing_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    # ---------------- DOWNLOAD TOKEN TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS download_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER,
        transaction_id INTEGER,
        file_path TEXT,
        format_type TEXT,
        created_at TEXT,
        expires_at TEXT,
        uses INTEGER DEFAULT 0,
        max_uses INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
    )
    """)

    # ---------------- DOWNLOAD ACTIVITY TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS download_activity (
        activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        transaction_id INTEGER,
        download_time TEXT,
        file_format TEXT,
        ip_address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (transaction_id) REFERENCES transactions(id)
    )
    """)

    conn.commit()
    conn.close()


# ✅ OPTIONAL: function to view all users (for admin page)
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id, username, email, created_at, last_login 
    FROM users
    """)

    users = cursor.fetchall()
    conn.close()

    return users


# ✅ OPTIONAL: function to delete user
def delete_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()