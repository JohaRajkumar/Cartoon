import streamlit as st
import sys
import os
import sqlite3

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from registration import init_session_state, logout_user
from database import DB_NAME  # canonical path

# ensure session keys exist
init_session_state()

NAV_ITEMS = [
    ("Register", "pages/register.py"),
    ("Login", "pages/login.py"),
    ("Upload Image", "pages/upload.py"),
    ("Dashboard", "pages/dashboard.py"),
    ("Profile", "pages/profile.py"),
    ("Gallery", "pages/gallery.py"),
    ("Admin", "pages/admin.py"),
    ("Forgot Password", "pages/forgot_password.py"),
]


def safe_switch_page(target):
    if not hasattr(st, "switch_page"):
        return False

    canonical = target.strip() if isinstance(target, str) else ""
    lean = canonical.lower().replace(" ", "_")
    mapping = {
        "register": "pages/register.py",
        "login": "pages/login.py",
        "upload": "pages/upload.py",
        "dashboard": "pages/dashboard.py",
        "profile": "pages/profile.py",
        "gallery": "pages/gallery.py",
        "admin": "pages/admin.py",
        "forgot_password": "pages/forgot_password.py",
        "forgot password": "pages/forgot_password.py",
    }

    candidates = [canonical]
    if canonical.startswith("pages/") and canonical.endswith(".py"):
        file_name = canonical.split("/")[-1][:-3]
        candidates += [file_name, file_name.replace("_", " ").title()]
    if canonical.endswith(".py"):
        file_name = canonical[:-3]
        candidates += [file_name, file_name.replace("_", " ").title()]
    candidates += [canonical.replace("_", " ").title(), lean]
    if lean in mapping:
        candidates.append(mapping[lean])
    if mapping.get(canonical.lower()):
        candidates.append(mapping[canonical.lower()])

    for candidate in candidates:
        if not candidate:
            continue
        try:
            st.switch_page(candidate)
            return True
        except Exception:
            pass

    return False


def hide_default_navigation():
    st.markdown(
        """
        <style>
        [data-testid=\"stSidebarNav\"] { visibility: hidden; height: 0; width: 0; }
        .css-1cpxqw2 { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_custom_sidebar():
    hide_default_navigation()
    st.sidebar.title("🎨 TOONIFY PRO")
    for label, target in NAV_ITEMS:
        if st.sidebar.button(label, key=f"nav-{label}"):
            if not safe_switch_page(target):
                st.warning("Navigation failed. Please use the sidebar links.")


render_custom_sidebar()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title=" 🎨TOONIFY PRO|Admin", page_icon="🛠")

st.markdown("<h2 style='text-align:center;'>🎨TOONIFY PRO</h2>", unsafe_allow_html=True)

# ---------- SESSION CHECK ----------
if not st.session_state.logged_in or not st.session_state.user:
    st.error("⚠ Please login first")
    st.page_link("pages/login.py", label="Go to Login")
    st.stop()

# ---------- SIDEBAR ----------
st.sidebar.markdown("## 🎨TOONIFY PRO")
st.sidebar.title("📌 Navigation")
st.sidebar.page_link("Dashboard", label="📊 Dashboard")
st.sidebar.page_link("Profile", label="👤 Profile")
st.sidebar.page_link("Admin", label="🛠 Admin")
st.sidebar.page_link("Login", label="🔐 Login")
st.sidebar.page_link("Register", label="📝 Register")

# ---------- ADMIN UI ----------
st.markdown('<div class="title">🛠 Admin Dashboard</div>', unsafe_allow_html=True)

st.write("### 👥 All Registered Users")

# ---------- FETCH USERS FROM DB ----------
try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username, email, created_at FROM users")
    users = cursor.fetchall()

    conn.close()

    if users:
        for user in users:
            st.write(f"🆔 {user[0]} | 👤 {user[1]} | 📧 {user[2]} | 🕒 {user[3]}")
    else:
        st.info("No users found")

except Exception as e:
    st.error(f"Database error: {e}")

# ---------- LOGOUT ----------
st.write("---")
if st.button("Logout"):
    logout_user()