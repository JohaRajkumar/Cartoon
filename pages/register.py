import streamlit as st
import re
import registration

from database import create_tables

# make sure our session helpers are available
registration.init_session_state()

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

# ensure database tables exist
create_tables()

# Staging: no external style module needed; custom sidebar already rendered.

st.markdown('<div class="title">📝 Register</div>', unsafe_allow_html=True)
st.set_page_config(page_title="🎨TOONIFY PRO|Register", page_icon="🎨", layout="centered")

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
body {
    background-color: #f5f7fa;
}
.main {
    background-color: white;
    padding: 30px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎨TOONIFY PRO")

# ---------- FUNCTIONS ----------
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)

def password_strength(password):
    strength = 0
    if len(password) >= 8:
        strength += 1
    if re.search("[A-Z]", password):
        strength += 1
    if re.search("[a-z]", password):
        strength += 1
    if re.search("[0-9]", password):
        strength += 1
    if re.search("[@#$%^&+=!]", password):
        strength += 1
    return strength

# ---------- INPUT FIELDS ----------
username = st.text_input("Username")
email = st.text_input("Email")

show_password = st.checkbox("Show Password")

if show_password:
    password = st.text_input("Password")
    confirm_password = st.text_input("Confirm Password")
else:
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

terms = st.checkbox("I agree to the Terms and Conditions")

# ---------- REAL-TIME VALIDATION ----------
if email:
    if is_valid_email(email):
        st.success("Valid Email ✅")
    else:
        st.error("Invalid Email ❌")

if password:
    strength = password_strength(password)
    if strength <= 2:
        st.error("Password Strength: Weak")
    elif strength == 3 or strength == 4:
        st.warning("Password Strength: Medium")
    else:
        st.success("Password Strength: Strong")

# ---------- REGISTER BUTTON ----------
if st.button("Register"):
    if not username or not email or not password:
        st.error("All fields are required")
    elif password != confirm_password:
        st.error("Passwords do not match")
    elif not terms:
        st.error("Please accept Terms & Conditions")
    else:
        success, message = registration.register_user(username, email, password)

        if success:
            st.success("🎉 Registration Successful!")
        else:
            st.error(message)

st.markdown("---")
st.markdown("👉 Already have an account? **Go to Login Page**")
st.markdown("---")

# switching pages requires the relative file path; plain "login" caused
# the StreamlitAPIException seen in the terminal.
if st.button("Already have an account? Login", key="goto_login"):
    st.switch_page("pages/login.py")

# The registration logic is handled above when the first "Register" button
# is clicked. The duplicate button here (with a different key) and the
# import from auth were unnecessary, so we've removed them to avoid
# confusion and reduce the chance of errors.
