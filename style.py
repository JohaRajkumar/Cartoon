import streamlit as st

def load_css():
    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(to right, #f5f7fa, #c3cfe2);
        font-family: 'Segoe UI', sans-serif;
    }

    .app-title {
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
    }

    .card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    div.stButton > button {
        background: #4CAF50;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
    }

    </style>
    """, unsafe_allow_html=True)


def session_state_get(key, default=None):
    """Safely retrieve session state value regardless of Streamlit runtime mode."""
    if hasattr(st.session_state, "get"):
        try:
            return st.session_state.get(key, default)
        except Exception:
            pass

    try:
        return st.session_state[key] if key in st.session_state else default
    except Exception:
        return default


def render_sidebar(user=None):
    """Render a consistent sidebar navigation across all pages.

    Use page file paths relative to the app root so Streamlit can find them.
    """
    st.sidebar.markdown("## 🎨TOONIFY PRO")
    st.sidebar.title("📌 Navigation")

    # authentication links change depending on login state
    if not user:
        st.sidebar.page_link("pages/register.py", label="📝 Register")
        st.sidebar.page_link("pages/login.py", label="🔐 Login")
    else:
        # show a logout button that uses our helper when clicked
        if st.sidebar.button("🚪 Logout"):
            try:
                from registration import logout_user
                logout_user()
            except Exception:
                pass

    # core app pages (these can still be accessed without login but may show
    # their own authorization checks)
    st.sidebar.page_link("pages/dashboard.py", label="📊 Dashboard")
    st.sidebar.page_link("pages/profile.py", label="👤 Profile")
    st.sidebar.page_link("pages/upload.py", label="📤 Upload Image")
    st.sidebar.page_link("pages/gallery.py", label="🖼 Gallery")
    st.sidebar.page_link("pages/admin.py", label="🛠 Admin")

    if user:
        st.sidebar.markdown("---")
        st.sidebar.write(f"Signed in as: {user}")

    # Add downloadable receipt to sidebar if payment was successful
    if session_state_get("payment_success", False):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📄 Receipt")
        
        # generate receipt content
        order_id = session_state_get("order_id", "N/A")
        payment_id = session_state_get("payment_id", "N/A")
        price = session_state_get("checkout_price", 0)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        receipt_text = f"""=================================
       TOONIFY PRO RECEIPT
=================================

Date: {timestamp}
Order ID: {order_id}
Payment ID: {payment_id}
Amount Paid: ₹{price}
User: {user if user else 'Guest'}
Status: SUCCESS

Thank you for your purchase!
================================="""
        
        st.sidebar.download_button(
            label="📥 Download Receipt",
            data=receipt_text,
            file_name=f"receipt_{order_id}.txt",
            mime="text/plain",
            key="sidebar_download_receipt"
        )