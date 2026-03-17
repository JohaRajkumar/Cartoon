import streamlit as st
import sys
import os

# path fix
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import create_tables

# ensure database tables exist
create_tables()

# custom sidebar navigation
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
    try:
        st.switch_page(target)
        return True
    except Exception:
        pass
    try:
        if target.endswith(".py"):
            t = target.split("/")[-1][:-3]
            st.switch_page(t)
            return True
        st.switch_page(target.replace("_", " ").title())
        return True
    except Exception:
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
                # Last-resort fallback to query param navigation for Streamlit pages.
                st.experimental_set_query_params(_page=target)
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
                else:
                    st.rerun()


render_custom_sidebar()

# authentication helpers
from registration import login_user, init_session_state

# make sure session_state has our auth keys
init_session_state()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title=" 🎨TOONIFY PRO|Login ", page_icon="🔐")

# ---------------- LOAD STYLE ----------------
st.markdown("<h2 style='text-align:center;'>🎨TOONIFY PRO</h2>", unsafe_allow_html=True)

# Custom sidebar is already rendered by render_custom_sidebar()

st.markdown('<div class="title">🔐 Login</div>', unsafe_allow_html=True)

identifier = st.text_input("Email or Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if not identifier.strip():
        st.error("Please provide your email or username")
    else:
        success, data = login_user(identifier, password)

        if success:
            # data is a dict containing user info
            st.session_state.logged_in = True
            st.session_state.user_id = data.get("user_id")
            st.session_state.user_email = data.get("email")
            st.session_state.user = data.get("username")

            st.success(f"Welcome {st.session_state.user} 🎉")
            st.page_link("pages/profile.py", label="➡ Go to Profile")
        else:
            # generic error message already provided by login_user
            st.error(data)

# ---------------- LOGIN UI ----------------
# ---------------- REGISTER LINK ----------------
st.write("---")
st.page_link("pages/register.py", label="New user? Register here")