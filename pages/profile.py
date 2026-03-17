import streamlit as st
import sys
import os

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------- IMPORTS ----------
import io
import datetime
import uuid

# auth helpers
from style import load_css, render_sidebar, session_state_get
from registration import init_session_state, logout_user

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

# make sure our auth keys exist
init_session_state()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🎨TOONIFY PRO|Profile ", page_icon="👤")

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

# ---------- PROFILE UI ----------
st.markdown('<div class="title">👤 User Profile</div>', unsafe_allow_html=True)

username = st.session_state.user

st.success(f"Welcome {username} 🎉")

st.write("### 📄 Your Details")
st.write(f"**Username / Email:** {username}")

# ---------- SETUP UPLOADS DIR ----------
ROOT = os.path.dirname(os.path.dirname(__file__))
uploads_dir = os.path.join(ROOT, "uploads")
os.makedirs(uploads_dir, exist_ok=True)

# ---------- PROFILE PICTURE ----------
profile_filename = f"profile_{username}.png"
profile_path = os.path.join(uploads_dir, profile_filename)

col1, col2 = st.columns([1, 2])
with col1:
    st.write("#### Profile Picture")
    if os.path.exists(profile_path):
        st.image(profile_path, width=180)
        if st.button("Remove avatar", key=f"remove_avatar_{username}"):
            try:
                os.remove(profile_path)
                st.success("Avatar removed")
                # trigger a rerun in a way that's compatible across Streamlit versions
                try:
                    if hasattr(st, "experimental_rerun"):
                        st.experimental_rerun()
                    else:
                        st.experimental_set_query_params(_r=uuid.uuid4().hex)
                except Exception:
                    st.session_state["_refresh"] = not session_state_get("_refresh", False)
            except Exception as e:
                st.error(f"Failed to remove avatar: {e}")
    else:
        st.write("No avatar yet")

    uploaded_avatar = st.file_uploader("Upload avatar (png/jpg)", type=["png", "jpg", "jpeg"], key="avatar_uploader")
    if uploaded_avatar is not None:
        data = uploaded_avatar.read()
        try:
            with open(profile_path, "wb") as f:
                f.write(data)
            st.success("Avatar saved")
            try:
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
                else:
                    st.experimental_set_query_params(_r=uuid.uuid4().hex)
            except Exception:
                st.session_state["_refresh"] = not session_state_get("_refresh", False)
        except Exception as e:
            st.error(f"Failed to save avatar: {e}")

with col2:
    # ---------- BIO ----------
    st.write("#### Bio")
    bio_path = os.path.join(uploads_dir, f"bio_{username}.txt")
    bio_text = ""
    if os.path.exists(bio_path):
        try:
            with open(bio_path, "r", encoding="utf-8") as f:
                bio_text = f.read()
        except Exception:
            bio_text = ""

    new_bio = st.text_area("Tell us about yourself", value=bio_text, height=120)
    if st.button("Save Bio", key=f"save_bio_{username}"):
        try:
            with open(bio_path, "w", encoding="utf-8") as f:
                f.write(new_bio)
            st.success("Bio saved")
        except Exception as e:
            st.error(f"Failed to save bio: {e}")

    # ---------- LOGOUT ----------
    if st.button("Logout", key="logout_button"):
        logout_user()  # clears session and reruns, redirect handled subsequently

# ---------- UPLOADS GALLERY ----------
st.markdown("---")
st.write("### 🖼️ Your Uploads & Recent Cartoons")

allowed = (".png", ".jpg", ".jpeg")
files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(allowed) and not f.startswith("profile_")]
files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(uploads_dir, x)), reverse=True)

if not files:
    st.info("No images in uploads yet. Upload one from the Upload page.")
else:
    cols = st.columns(3)
    for i, fname in enumerate(files):
        path = os.path.join(uploads_dir, fname)
        col = cols[i % 3]
        with col:
            try:
                st.image(path, width=300)
            except Exception:
                st.write(fname)

            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
            st.write(f"**{fname}**")
            st.write(f"Uploaded: {mtime}")

            # Download button
            try:
                with open(path, "rb") as f:
                    data = f.read()
                st.download_button(label="Download", data=data, file_name=fname, key=f"dl_{fname}")
            except Exception:
                st.warning("Download unavailable")

            # Delete button
            if st.button("Delete", key=f"del_{fname}"):
                try:
                        os.remove(path)
                        st.success(f"Deleted {fname}")
                        try:
                            if hasattr(st, "experimental_rerun"):
                                st.experimental_rerun()
                            else:
                                st.experimental_set_query_params(_r=uuid.uuid4().hex)
                        except Exception:
                            st.session_state["_refresh"] = not session_state_get("_refresh", False)
                except Exception as e:
                    st.error(f"Failed to delete: {e}")

    st.write(f"\n**Total images:** {len(files)}")