import streamlit as st
import os
from PIL import Image

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🎨TOONIFY PRO|Gallery", page_icon="🖼️", layout="wide")

# ---------- CUSTOM CSS ----------
from style import load_css, session_state_get
load_css()

st.markdown("<h1 style='text-align:center;'>🖼 Gallery</h1>", unsafe_allow_html=True)

# custom sidebar navigation
from registration import init_session_state
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

# ensure session user
if not st.session_state.logged_in or not st.session_state.user:
    st.error("⚠ Please login first")
    st.stop()

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
uploads_dir = os.path.abspath(uploads_dir)

if not os.path.isdir(uploads_dir):
    st.info("No images have been uploaded yet.")
else:
    files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    # ---------- MANAGE UPLOADS ----------
    with st.expander("Manage uploads"):
        st.write("Delete all uploaded images (this action is irreversible)")
        if files:
            confirm_text = st.text_input("Type DELETE to confirm", key="delete_confirm")
            if st.button("Delete All Uploads"):
                if confirm_text == "DELETE":
                    deleted = 0
                    for fname in files:
                        try:
                            os.remove(os.path.join(uploads_dir, fname))
                            deleted += 1
                        except Exception:
                            continue
                    st.success(f"Deleted {deleted} files")
                    try:
                        if hasattr(st, "experimental_rerun"):
                            st.experimental_rerun()
                        else:
                            import uuid
                            st.experimental_set_query_params(_r=uuid.uuid4().hex)
                    except Exception:
                        st.session_state["_refresh"] = not session_state_get("_refresh", False)
                else:
                    st.error("Confirmation text did not match. Type DELETE to confirm.")
        else:
            st.info("No uploaded images to delete")
    if not files:
        st.info("No images found in uploads.")
    else:
        cols = st.columns(3)
        for idx, fname in enumerate(files):
            path = os.path.join(uploads_dir, fname)
            try:
                img = Image.open(path)
                with cols[idx % 3]:
                    # `use_column_width` is deprecated; use an explicit pixel width instead.
                    # 300px is a reasonable default for a 3-column gallery.
                    st.image(img, caption=fname, width=300)
            except Exception:
                continue

# navigation back to dashboard
if st.button("⬅ Back to Dashboard"):
    st.switch_page("pages/dashboard.py")