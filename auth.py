import sqlite3
import hashlib
import re
from datetime import datetime

import os
DB_NAME = os.path.join(os.path.dirname(__file__), "app.db")

# ---------------- PASSWORD HASH ----------------
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------- VALIDATIONS ----------------
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    if not re.search("[@#$%^&+=!]", password):
        return False
    return True


# ---------------- REGISTER USER ----------------
def register_user(username, email, password):
    try:
        # normalize input
        username = username.strip().lower()
        email = email.strip().lower()

        # validations
        if username == "":
            return False, "Username required"

        if not is_valid_email(email):
            return False, "Invalid email format"

        if not is_strong_password(password):
            return False, "Password must be 8+ chars with A-Z, a-z, 0-9 & special char"

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # check duplicate (case-insensitive)
        cursor.execute(
            "SELECT user_id FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?",
            (email, username)
        )

        if cursor.fetchone():
            conn.close()
            return False, "User already exists"

        # hash password
        hashed_password = hash_password(password)

        # insert
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, email, hashed_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()

        return True, "Registration successful ✅"

    except sqlite3.IntegrityError:
        return False, "Email already registered"

    except Exception as e:
        return False, f"Database error: {e}"


# ---------------- LOGIN USER ----------------
def login_user(email, password):
    try:
        lookup = email.strip().lower()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password_hash FROM users WHERE LOWER(email) = ?",
            (lookup,)
        )

        user = cursor.fetchone()
        conn.close()

        if not user:
            return False, "User not found"

        username, stored_hash = user

        # verify password
        if hash_password(password) != stored_hash:
            return False, "Invalid password"

        return True, username

    except Exception as e:
        return False, str(e)


# ---------------- RESET PASSWORD ----------------
def reset_password(email, new_password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # check user exists
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return False, "User not found"

        # validate password
        if not is_strong_password(new_password):
            conn.close()
            return False, "Weak password"

        # hash new password
        new_hash = hash_password(new_password)

        # update password
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, failed_attempts = 0, is_locked = 0
            WHERE email = ?
        """, (new_hash, email))

        conn.commit()
        conn.close()

        return True, "Password reset successful ✅"

    except Exception as e:
        return False, str(e)
