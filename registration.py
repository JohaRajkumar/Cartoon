import sqlite3
import hashlib
import re
from datetime import datetime
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "app.db")

# ---------------- PASSWORD HASH ----------------
def hash_password(password: str) -> str:
    """Return SHA256 hex digest of *password*."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------- VALIDATION HELPERS ----------------
_email_re = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

def is_valid_email(email: str) -> bool:
    return bool(_email_re.match(email))


def is_strong_password(password: str) -> bool:
    """Simple strength check used at registration.

    Matches the previous password_strength logic from the UI.
    """
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
def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """Create a new user record.

    The incoming data is normalized (trimmed + lower‑cased) before the
    duplicate check.  Passwords are hashed with SHA256 and never stored in
    plain text.

    Returns ``(True, message)`` on success; on failure the boolean is false and
    the message can be displayed directly to the user.
    """

    # basic validation so the caller doesn't need to duplicate this logic
    if not username.strip():
        return False, "Name is required"
    if not email.strip() or not is_valid_email(email):
        return False, "A valid email address is required"
    if not password:
        return False, "Password is required"
    if not is_strong_password(password):
        return False, "Password must be 8+ chars with upper, lower, number and symbol"

    # normalize for storage / comparison
    username_norm = username.strip().lower()
    email_norm = email.strip().lower()

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # case‑insensitive duplicate check
        cursor.execute(
            "SELECT user_id FROM users WHERE LOWER(email)=? OR LOWER(username)=?",
            (email_norm, username_norm),
        )
        if cursor.fetchone():
            conn.close()
            return False, "Account already exists. Please login."

        hashed_password = hash_password(password)
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                username_norm,
                email_norm,
                hashed_password,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()
        return True, "Registration successful"

    except sqlite3.IntegrityError:
        # should not normally happen due to pre‑check, but be safe
        return False, "Account already exists. Please login."
    except Exception as e:
        return False, f"Database error: {e}"


# ---------------- LOGIN USER ----------------
def login_user(identifier: str, password: str):
    """Authenticate a user by email or username.

    Returns ``(True, info_dict)`` where ``info_dict`` contains ``user_id``,
    ``username`` and ``email`` when credentials are valid.  Otherwise a
    generic error message is returned so callers cannot distinguish between an
    unknown user and a bad password.
    """

    lookup = identifier.strip().lower()
    if not lookup or not password:
        return False, "Invalid email or password."

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, username, email, password_hash, failed_attempts, is_locked
            FROM users
            WHERE LOWER(email)=? OR LOWER(username)=?
            """,
            (lookup, lookup),
        )
        user = cursor.fetchone()

        if not user:
            conn.close()
            return False, "Invalid email or password."

        user_id, username_norm, email_norm, stored_hash, failed_attempts, is_locked = user

        if is_locked == 1:
            conn.close()
            return False, "Account locked due to too many failed attempts"

        if hash_password(password) != stored_hash:
            failed_attempts += 1
            cursor.execute(
                "UPDATE users SET failed_attempts=?, is_locked=? WHERE user_id=?",
                (failed_attempts, 1 if failed_attempts >= 5 else 0, user_id),
            )
            conn.commit()
            conn.close()
            return False, "Invalid email or password."

        # correct password; reset counters and record last login
        cursor.execute(
            "UPDATE users SET failed_attempts=0, last_login=? WHERE user_id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id),
        )
        conn.commit()
        conn.close()

        return True, {"user_id": user_id, "username": username_norm, "email": email_norm}

    except Exception as e:
        return False, f"Database error: {e}"


# ---------------- SESSION HELPERS ----------------
def init_session_state():
    """Ensure authentication-related keys exist in ``st.session_state``."""
    try:
        import streamlit as st
    except ImportError:
        return

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "user" not in st.session_state:
        st.session_state.user = None


def logout_user():
    """Clear auth-related session_state keys and rerun page."""
    try:
        import streamlit as st
    except ImportError:
        return

    for key in ("logged_in", "user_id", "user_email", "user"):
        if key in st.session_state:
            del st.session_state[key]
    try:
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            # some versions call this newer helper; guard as well
            if hasattr(st, "experimental_set_query_params"):
                st.experimental_set_query_params(_r=1)
            elif hasattr(st, "rerun"):
                st.rerun()
    except Exception:
        pass
