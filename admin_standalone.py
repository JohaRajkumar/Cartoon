import streamlit as st
import sys
import os
import sqlite3

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from style import load_css, render_sidebar, session_state_get
from registration import init_session_state, logout_user
from database import DB_NAME

# make sure session state keys exist
init_session_state()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title=" 🎨TOONIFY PRO|Admin", page_icon="🛠")

# ---------- LOAD CSS ----------
load_css()
st.markdown("<h2 style='text-align:center;'>🎨TOONIFY PRO</h2>", unsafe_allow_html=True)

# ---------- SESSION CHECK ----------
if not st.session_state.logged_in or not st.session_state.user:
    st.error("⚠ Please login first")
    st.page_link("pages/login.py", label="Go to Login")
    st.stop()

# ---------- SIDEBAR ----------
render_sidebar(session_state_get("user"))

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