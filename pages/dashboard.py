import streamlit as st
import sys
import os
import sqlite3

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------- SESSION INIT ----------
from registration import init_session_state, logout_user
from database import DB_NAME, create_tables
from style import load_css
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
    page_root = os.path.dirname(__file__)

    # Make a set of candidate page targets to try.
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

    candidates = []

    if canonical:
        candidates.append(canonical)

    if canonical.startswith("pages/") and canonical.endswith(".py"):
        file_name = canonical.split("/")[-1][:-3]
        candidates.append(file_name)
        candidates.append(file_name.replace("_", " ").title())

    if canonical.endswith(".py"):
        file_name = canonical[:-3]
        candidates.append(file_name)
        candidates.append(file_name.replace("_", " ").title())

    candidates.append(canonical.replace("_", " ").title())
    candidates.append(lean)

    if lean in mapping:
        candidates.append(mapping[lean])

    # Always include mapped page if not already in candidates
    if mapping.get(canonical.lower()):
        candidates.append(mapping[canonical.lower()])

    for candidate in candidates:
        if not candidate:
            continue
        try:
            st.switch_page(candidate)
            return True
        except Exception:
            continue

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


def session_state_get(key, default=None):
    if hasattr(st.session_state, "get"):
        try:
            return st.session_state.get(key, default)
        except Exception:
            pass
    try:
        return st.session_state[key] if key in st.session_state else default
    except Exception:
        return default


render_custom_sidebar()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title=" 🎨TOONIFY PRO|Dashboard ", page_icon="📊", layout="wide")

# ---------- LOAD CSS ----------
load_css()
st.markdown("<h2 style='text-align:center;'>🎨TOONIFY PRO</h2>", unsafe_allow_html=True)

# ---------- LOGIN CHECK ----------
if not st.session_state.logged_in or not st.session_state.user:
    st.error("⚠ Please login first")
    st.stop()

# ---------- SIDEBAR ----------
# We use only the custom TOONIFY PRO left sidebar here.
# render_sidebar(session_state_get("user"))

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>📊 Dashboard</h1>", unsafe_allow_html=True)
st.success(f"Welcome {session_state_get('user')} 🎉")

# Ensure tables exist so metrics can be loaded safely.
try:
    create_tables()
except Exception:
    st.warning("Could not initialize database tables for dashboard metrics.")

# ---------- METRICS ----------
user_count = None
transaction_count = None
cartoon_count = None

try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions")
    transaction_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM image_history")
    cartoon_count = cursor.fetchone()[0]

    conn.close()
except Exception as exc:
    st.error(f"Dashboard metric retrieval failed: {exc}")

col1, col2, col3 = st.columns(3)

if user_count is not None:
    col1.metric("Total users", user_count)
else:
    col1.write("Total users: -")

if transaction_count is not None:
    col2.metric("Total transactions", transaction_count)
else:
    col2.write("Total transactions: -")

if cartoon_count is not None:
    col3.metric("Saved cartoons", cartoon_count)
else:
    col3.write("Saved cartoons: -")

st.markdown("---")

st.write("### 📌 Quick links")
if st.button("Go to Upload"):
    safe_switch_page("pages/upload.py")
if st.button("View Gallery"):
    safe_switch_page("pages/gallery.py")
if st.button("Profile"):
    safe_switch_page("pages/profile.py")

st.write("### 🕒 Your recent cartoons")
try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    username = session_state_get("user")

    cursor.execute("SELECT original_image_path, processed_image_path, style_applied, processing_date FROM image_history WHERE user_id = (SELECT user_id FROM users WHERE username = ?) ORDER BY processing_date DESC LIMIT 5", (username,))
    recent = cursor.fetchall()
    conn.close()

    if recent:
        for orig, proc, style, date in recent:
            st.write(f"- {date}: {style} (orig: {orig}, proc: {proc})")
    else:
        st.info("No recent cartoons yet; go to Upload to create one.")
except Exception:
    st.info("No personal cartoon history available yet.")