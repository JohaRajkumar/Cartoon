import io
import datetime
import streamlit as st

# ── optional imports ──────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

from style import load_css, render_sidebar
from payment_gateway import verify_payment_signature, update_transaction_status


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def session_state_get(key, default=None):
    try:
        return st.session_state.get(key, default)
    except Exception:
        try:
            return st.session_state[key] if key in st.session_state else default
        except Exception:
            return default


def initialize_session():
    defaults = {
        "payment_success": False,
        "payment_status": None,
        "processed_image": None,
        "order_id": None,
        "payment_id": None,
        "transaction_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def verify_to_session(order_id, payment_id, signature):
    verified = False
    try:
        verified = verify_payment_signature(order_id, payment_id, signature)
    except Exception:
        verified = False

    base_vals = {
        "order_id": order_id,
        "payment_id": payment_id,
        "transaction_id": payment_id,
    }
    for k, v in base_vals.items():
        st.session_state[k] = v

    if verified:
        st.session_state.payment_status = "success"
        st.session_state.payment_success = True
        st.session_state.selected_style = session_state_get("current_style", "Unknown")
        try:
            amount = int(session_state_get("checkout_price", 0) * 100)
            update_transaction_status(
                order_id, payment_id, "success", amount,
                user_id=session_state_get("user", "unknown")
            )
        except Exception:
            pass
        paid_key = (
            f"paid_{session_state_get('uploaded_filename', '')}"
            f"_{session_state_get('current_style', '')}"
        )
        st.session_state[paid_key] = True
        return True

    st.session_state.payment_status = "failed"
    st.session_state.payment_success = False
    try:
        amount = int(session_state_get("checkout_price", 0) * 100)
        update_transaction_status(
            order_id, payment_id, "failed", amount,
            user_id=session_state_get("user", "unknown")
        )
    except Exception:
        pass
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Receipt generators
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf_receipt(order_id, payment_id, amount, timestamp, user):
    """Generate a nicely styled PDF receipt using reportlab."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # ── background ──
    c.setFillColor(colors.HexColor("#0F0F1A"))
    c.rect(0, 0, w, h, fill=True, stroke=False)

    # ── top accent band ──
    c.setFillColor(colors.HexColor("#6C63FF"))
    c.rect(0, h - 18 * mm, w, 18 * mm, fill=True, stroke=False)

    # ── gradient-like accent stripe ──
    for i, hex_col in enumerate(["#6C63FF", "#7B74FF", "#8A85FF", "#9996FF"]):
        c.setFillColor(colors.HexColor(hex_col))
        c.rect(0, h - (18 + i * 1.5) * mm, w, 1.5 * mm, fill=True, stroke=False)

    # ── logo text ──
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 12 * mm, "🎨  TOONIFY PRO")

    # ── subtitle ──
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#B0B8FF"))
    c.drawCentredString(w / 2, h - 24 * mm, "Official Payment Receipt")

    # ── success badge ──
    badge_y = h - 42 * mm
    c.setFillColor(colors.HexColor("#1A2A1A"))
    c.roundRect(w / 2 - 45, badge_y, 90, 14 * mm, 7, fill=True, stroke=False)
    c.setFillColor(colors.HexColor("#48C9B0"))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w / 2, badge_y + 4 * mm, "✔  PAYMENT SUCCESSFUL")

    # ── divider ──
    c.setStrokeColor(colors.HexColor("#2A2A4A"))
    c.setLineWidth(1)
    c.line(20 * mm, h - 54 * mm, w - 20 * mm, h - 54 * mm)

    # ── receipt details ──
    details = [
        ("Date & Time",  timestamp),
        ("Order ID",     order_id),
        ("Payment ID",   payment_id),
        ("Amount Paid",  f"₹{amount}"),
        ("Status",       "SUCCESS"),
        ("Customer",     user),
        ("Product",      "Cartoon Image – HD Download"),
    ]

    row_h = 12 * mm
    start_y = h - 62 * mm

    for i, (label, value) in enumerate(details):
        y = start_y - i * row_h
        # alternating row shade
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#16162A"))
            c.rect(18 * mm, y - 3 * mm, w - 36 * mm, row_h, fill=True, stroke=False)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#9999CC"))
        c.drawString(22 * mm, y + 3 * mm, label.upper())

        c.setFont("Helvetica", 10)
        if label == "Status":
            c.setFillColor(colors.HexColor("#48C9B0"))
        elif label == "Amount Paid":
            c.setFillColor(colors.HexColor("#F9CA74"))
        else:
            c.setFillColor(colors.white)
        c.drawRightString(w - 22 * mm, y + 3 * mm, str(value))

    # ── bottom divider ──
    bottom_y = start_y - len(details) * row_h - 6 * mm
    c.setStrokeColor(colors.HexColor("#2A2A4A"))
    c.line(20 * mm, bottom_y, w - 20 * mm, bottom_y)

    # ── footer note ──
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#6666AA"))
    c.drawCentredString(w / 2, bottom_y - 8 * mm,
                        "This is a computer-generated receipt and requires no signature.")
    c.drawCentredString(w / 2, bottom_y - 14 * mm,
                        "For support, contact support@toonifypro.com")

    # ── bottom accent band ──
    c.setFillColor(colors.HexColor("#6C63FF"))
    c.rect(0, 0, w, 8 * mm, fill=True, stroke=False)

    c.save()
    buf.seek(0)
    return buf


def generate_image_receipt(order_id, payment_id, amount, timestamp, user):
    """Fallback PNG receipt when reportlab is not available."""
    img = Image.new("RGB", (600, 420), color=(15, 15, 26))
    d = ImageDraw.Draw(img)

    # header bar
    d.rectangle([0, 0, 600, 70], fill=(108, 99, 255))
    font = ImageFont.load_default()
    d.text((210, 22), "TOONIFY PRO", fill=(255, 255, 255), font=font)
    d.text((210, 45), "Official Payment Receipt", fill=(180, 180, 255), font=font)

    # success badge
    d.rounded_rectangle([180, 90, 420, 130], radius=8, fill=(26, 42, 26))
    d.text((220, 105), "PAYMENT SUCCESSFUL", fill=(72, 201, 176), font=font)

    details = [
        ("Date & Time",  timestamp),
        ("Order ID",     order_id),
        ("Payment ID",   payment_id),
        ("Amount Paid",  f"INR {amount}"),
        ("Status",       "SUCCESS"),
        ("Customer",     user),
    ]
    y = 150
    for label, value in details:
        d.text((40, y), f"{label}:", fill=(153, 153, 204), font=font)
        d.text((220, y), str(value), fill=(255, 255, 255), font=font)
        y += 30

    d.text((100, 390), "This is a computer-generated receipt.", fill=(100, 100, 170), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.success-hero {
    background: linear-gradient(135deg, #0F0F1A 0%, #1A1A3A 100%);
    border: 1px solid #6C63FF44;
    border-radius: 20px;
    padding: 48px 40px 40px;
    text-align: center;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.success-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #6C63FF, #48C9B0);
}
.success-hero h1 {
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #6C63FF, #48C9B0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 12px;
}
.success-hero p {
    color: #9999CC;
    font-size: 1.05rem;
}

.receipt-card {
    background: linear-gradient(145deg, #13132A, #1A1A3A);
    border: 1px solid #2A2A5A;
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 24px;
}
.receipt-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #1E1E3A;
}
.receipt-row:last-child { border-bottom: none; }
.receipt-label {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #6666AA;
    text-transform: uppercase;
}
.receipt-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #E0E0FF;
}
.amount-val { color: #F9CA74 !important; font-size: 1.1rem !important; }
.status-val { color: #48C9B0 !important; }

.dl-btn-wrap {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-top: 16px;
}

.confetti-anim {
    font-size: 3rem;
    animation: pop 0.6s ease-out;
}
@keyframes pop {
    0%   { transform: scale(0); opacity: 0; }
    70%  { transform: scale(1.2); }
    100% { transform: scale(1); opacity: 1; }
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="✅ Payment Success – TOONIFY PRO", layout="wide")

    initialize_session()
    try:
        load_css()
    except Exception:
        pass
    try:
        render_sidebar(session_state_get("user"))
    except Exception:
        pass

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Read query params (Razorpay redirects here with payment details) ──────
    params = {}
    try:
        params = st.query_params   # Streamlit ≥ 1.30
    except AttributeError:
        try:
            params = st.experimental_get_query_params()
        except Exception:
            params = {}

    def _param(key):
        val = params.get(key, None)
        if val is None:
            return None
        if isinstance(val, list):
            return val[0]
        return val

    payment_id_param = _param("payment_id")
    order_id_param   = _param("order_id")
    signature_param  = _param("signature")
    cancelled        = _param("payment_cancelled")

    # ── Handle cancellation ───────────────────────────────────────────────────
    if cancelled:
        st.session_state.payment_success = False
        st.session_state.payment_status  = "failed"
        st.warning("⚠️ Payment was cancelled. Please try again from the checkout page.")
        if st.button("← Back to Checkout"):
            try:
                st.switch_page("pages/checkout.py")
            except Exception:
                st.info("Please navigate to the Checkout page manually.")
        return

    # ── Verify incoming params if not already verified ────────────────────────
    if payment_id_param and order_id_param and signature_param:
        if session_state_get("payment_status") not in ("success", "failed"):
            with st.spinner("🔒 Verifying your payment…"):
                ok = verify_to_session(order_id_param, payment_id_param, signature_param)
            if not ok:
                st.error("❌ Payment verification failed. Please contact support.")
                return

            # Clear query params after processing
            try:
                st.query_params.clear()
            except Exception:
                try:
                    st.experimental_set_query_params()
                except Exception:
                    pass

    # ── Guard: not paid yet ───────────────────────────────────────────────────
    if not session_state_get("payment_success", False):
        st.markdown("""
        <div class='success-hero'>
            <h1>🛒 No Payment Found</h1>
            <p>Looks like you haven't completed checkout yet, or your session expired.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Checkout →"):
            try:
                st.switch_page("pages/checkout.py")
            except Exception:
                st.info("Please navigate to the Checkout page manually.")
        return

    # ── Payment confirmed ─────────────────────────────────────────────────────
    order_id   = session_state_get("order_id",   "N/A")
    payment_id = session_state_get("payment_id", "N/A")
    price      = session_state_get("checkout_price", 0)
    user       = session_state_get("user", "Guest")
    timestamp  = datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S")

    # Hero banner
    st.markdown(f"""
    <div class='success-hero'>
        <div class='confetti-anim'>🎉</div>
        <h1>Payment Successful!</h1>
        <p>Thank you for your purchase. Your receipt is ready to download below.</p>
    </div>
    """, unsafe_allow_html=True)

    # Receipt card
    st.markdown(f"""
    <div class='receipt-card'>
        <div class='receipt-row'>
            <span class='receipt-label'>Date &amp; Time</span>
            <span class='receipt-value'>{timestamp}</span>
        </div>
        <div class='receipt-row'>
            <span class='receipt-label'>Order ID</span>
            <span class='receipt-value'>{order_id}</span>
        </div>
        <div class='receipt-row'>
            <span class='receipt-label'>Payment ID</span>
            <span class='receipt-value'>{payment_id}</span>
        </div>
        <div class='receipt-row'>
            <span class='receipt-label'>Amount Paid</span>
            <span class='receipt-value amount-val'>₹ {price}</span>
        </div>
        <div class='receipt-row'>
            <span class='receipt-label'>Status</span>
            <span class='receipt-value status-val'>✔ SUCCESS</span>
        </div>
        <div class='receipt-row'>
            <span class='receipt-label'>Customer</span>
            <span class='receipt-value'>{user}</span>
        </div>
        <div class='receipt-row'>
            <span class='receipt-label'>Product</span>
            <span class='receipt-value'>Cartoon Image – HD Download</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Download buttons ──────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Download Receipt")
        if HAS_REPORTLAB:
            pdf_buf = generate_pdf_receipt(order_id, payment_id, price, timestamp, user)
            st.download_button(
                label="⬇️ Download Receipt (PDF)",
                data=pdf_buf,
                file_name=f"TOONIFY_Receipt_{order_id}.pdf",
                mime="application/pdf",
                key="dl_receipt_pdf",
                use_container_width=True,
            )
        elif HAS_PIL:
            img_buf = generate_image_receipt(order_id, payment_id, price, timestamp, user)
            st.download_button(
                label="⬇️ Download Receipt (PNG)",
                data=img_buf,
                file_name=f"TOONIFY_Receipt_{order_id}.png",
                mime="image/png",
                key="dl_receipt_img",
                use_container_width=True,
            )
        else:
            receipt_txt = (
                f"TOONIFY PRO – PAYMENT RECEIPT\n"
                f"================================\n"
                f"Date     : {timestamp}\n"
                f"Order ID : {order_id}\n"
                f"Pay ID   : {payment_id}\n"
                f"Amount   : INR {price}\n"
                f"Status   : SUCCESS\n"
                f"Customer : {user}\n"
                f"================================\n"
            )
            st.download_button(
                label="⬇️ Download Receipt (TXT)",
                data=receipt_txt,
                file_name=f"TOONIFY_Receipt_{order_id}.txt",
                mime="text/plain",
                key="dl_receipt_txt",
                use_container_width=True,
            )

    with col2:
        st.markdown("#### 🖼️ Download Cartoon Image")
        cartoon_bytes = session_state_get("processed_image")

        if not cartoon_bytes and session_state_get("adjusted_image") is not None:
            try:
                import cv2
                _, buf_img = cv2.imencode(".png", session_state_get("adjusted_image"))
                cartoon_bytes = buf_img.tobytes()
            except Exception:
                cartoon_bytes = None

        if cartoon_bytes:
            st.download_button(
                label="⬇️ Download Cartoon Image",
                data=cartoon_bytes,
                file_name="cartoon_processed.png",
                mime="image/png",
                key="dl_cartoon",
                use_container_width=True,
            )
        else:
            st.info("Processed image not in session cache — use Secure Download Hub below.")

        st.markdown("---")
        if st.button("🔐 Go to Secure Download Hub", use_container_width=True):
            try:
                st.switch_page("pages/download.py")
            except Exception:
                st.info("Please navigate to the Download page manually.")


if __name__ == "__main__":
    main()
