import streamlit as st
import sys
import os

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------- IMPORTS ----------
from auth import reset_password

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title=" 🎨TOONIFY PRO|Forgot Password", page_icon="🔑")

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
            st.switch_page(target)


render_custom_sidebar()

st.markdown("<h2 style='text-align:center;'>🎨TOONIFY PRO</h2>", unsafe_allow_html=True)

# ---------- UI ----------
st.markdown('<div class="title">🔑 Reset Password</div>', unsafe_allow_html=True)

email = st.text_input("Enter your registered email")
new_password = st.text_input("Enter new password", type="password")
confirm_password = st.text_input("Confirm new password", type="password")

# ---------- BUTTON ----------
if st.button("Reset Password"):
    success, msg = reset_password(email, new_password)
    if success:
            st.success(msg)
    else:
            st.error(msg)

    if email == "" or new_password == "" or confirm_password == "":
        st.warning("All fields are required")

    elif new_password != confirm_password:
        st.error("Passwords do not match")

    else:
        result = reset_password(email, new_password)

        if result == "Password updated successfully":
            st.success(result)
            st.page_link("pages/login.py", label="Go to Login")
        else:
            st.error(result)

# ---------- LOGIN LINK ----------
st.write("---")
st.page_link("pages/login.py", label="Back to Login")