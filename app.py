import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# initialize session state keys
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "image_processed" not in st.session_state:
    st.session_state.image_processed = False
if "checkout_allowed" not in st.session_state:
    st.session_state.checkout_allowed = False
if "payment_success" not in st.session_state:
    st.session_state.payment_success = False
if "order_id" not in st.session_state:
    st.session_state.order_id = None
if "payment_id" not in st.session_state:
    st.session_state.payment_id = None
if "processed_image" not in st.session_state:
    st.session_state.processed_image = None

# Hide default Streamlit pages list from sidebar
st.markdown(
    """
    <style>
    [data-testid=\"stSidebarNav\"] { visibility: hidden; height: 0; width: 0; }
    .css-1cpxqw2 { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("🎨 TOONIFY PRO")


def safe_switch_page(target):
    """Try both file path and page name forms for st.switch_page."""
    if not hasattr(st, "switch_page"):
        return False
    try:
        st.switch_page(target)
        return True
    except Exception:
        pass

    try:
        # convert pages/foo.py to foo (or fallback with spaces)
        if target.startswith("pages/") and target.endswith(".py"):
            page_name = target.split("/")[-1][:-3]
            st.switch_page(page_name)
            return True
        if target.endswith(".py"):
            st.switch_page(target[:-3])
            return True
    except Exception:
        pass

    # As a last resort try visible label-based switch
    try:
        label = target.replace("pages/", "").replace(".py", "").replace("_", " ").title()
        st.switch_page(label)
        return True
    except Exception:
        return False


nav_items = [
    ("Register", "pages/register.py"),
    ("Login", "pages/login.py"),
    ("Upload Image", "pages/upload.py"),
    ("Dashboard", "pages/dashboard.py"),
    ("Profile", "pages/profile.py"),
    ("Gallery", "pages/gallery.py"),
    ("Admin", "pages/admin.py"),
    ("Forgot Password", "pages/forgot_password.py"),
]

for label, target in nav_items:
    if st.sidebar.button(label, key=f"nav-{label}"):
        if not safe_switch_page(target):
            st.experimental_set_query_params(_page=label)
            if hasattr(st, "experimental_rerun"):
                st.experimental_rerun()
            elif hasattr(st, "rerun"):
                st.rerun()

st.header("🎨 TOONIFY PRO")
st.write("Use the sidebar to navigate through the app.")
