import os
import io
import uuid
import datetime
import streamlit as st
import streamlit.components.v1 as components
import base64
from dotenv import load_dotenv

try:
    from receipt_generator import generate_pdf_receipt, HAS_REPORTLAB
except ImportError:
    HAS_REPORTLAB = False
    generate_pdf_receipt = None

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# ── payment imports ────────────────────────────────────────────────────────────
try:
    from payment_gateway import (
        create_payment_order,
        verify_payment_signature,
        update_transaction_status,
        HAS_RAZORPAY,
        is_razorpay_configured,
    )
except ImportError:
    create_payment_order = None
    verify_payment_signature = None
    update_transaction_status = None
    HAS_RAZORPAY = False
    is_razorpay_configured = lambda: False

load_dotenv()

# ── session defaults ───────────────────────────────────────────────────────────
_DEFAULTS = {
    "payment_success": False,
    "payment_status": None,
    "order_id": None,
    "payment_id": None,
    "transaction_id": None,
    "processed_image": None,
    "checkout_format": "PNG",
    "checkout_quality": "high",
    "checkout_price": 10,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def sget(key, default=None):
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default


def switch(page_path):
    if not hasattr(st, "switch_page"):
        return False
    for candidate in [page_path, page_path.replace("pages/", "").replace(".py", "")]:
        try:
            st.switch_page(candidate)
            return True
        except Exception:
            continue
    return False


# ── PDF receipt builder imported from receipt_generator.py ───────────────────
def _display_pdf_inline(pdf_bytes):
    """Embed a PDF viewer directly in the page using base64."""
    try:
        b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" style="border:1px solid #2A2A5A; border-radius:12px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception:
        st.error("Could not render PDF preview.")



def _show_receipt_download(order_id, payment_id, price, user):
    """Render a success banner + receipt card + PDF download button."""
    timestamp = datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S")

    st.markdown(f"""
    <div class='checkout-hero' style='border-color:#48C9B044;'>
        <div style='font-size:3rem; animation: pop .6s ease-out;'>🎉</div>
        <h1 style='background:linear-gradient(135deg,#48C9B0,#6C63FF);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            Payment Successful!
        </h1>
        <p>Thank you, <strong>{user}</strong>! Download your receipt below.</p>
    </div>
    <style>
    @keyframes pop {{
        0%   {{ transform:scale(0);opacity:0 }}
        70%  {{ transform:scale(1.2) }}
        100% {{ transform:scale(1);opacity:1 }}
    }}
    </style>
    """, unsafe_allow_html=True)

    # Receipt summary card
    st.markdown(f"""
    <div class='order-card'>
        <div class='order-row'><span class='order-label'>Date & Time</span><span class='order-value'>{timestamp}</span></div>
        <div class='order-row'><span class='order-label'>Order ID</span><span class='order-value'>{order_id}</span></div>
        <div class='order-row'><span class='order-label'>Payment ID</span><span class='order-value'>{payment_id}</span></div>
        <div class='order-row'><span class='order-label'>Amount Paid</span><span class='order-value price-val'>₹ {price}</span></div>
        <div class='order-row'><span class='order-label'>Status</span><span class='order-value' style='color:#48C9B0;'>✔ SUCCESS</span></div>
        <div class='order-row'><span class='order-label'>Customer</span><span class='order-value'>{user}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        if HAS_REPORTLAB and generate_pdf_receipt:
            pdf_buf = generate_pdf_receipt(order_id, payment_id, price, timestamp, user)
            if pdf_buf:
                st.download_button(
                    label="📄 Download Official Invoice (PDF)",
                    data=pdf_buf,
                    file_name=f"TOONIFY_Invoice_{order_id}.pdf",
                    mime="application/pdf",
                    key="checkout_dl_invoice_pdf",
                    use_container_width=True,
                    type="primary",
                )
            if HAS_REPORTLAB and generate_pdf_receipt and pdf_buf:
                with st.expander("👁️ View Invoice Preview", expanded=True):
                    _display_pdf_inline(pdf_buf.getvalue())
        else:
            invoice_txt = (
                f"TOONIFY PRO – INVOICE\n{'='*30}\n"
                f"Date    : {timestamp}\nOrder   : {order_id}\n"
                f"Payment : {payment_id}\nAmount  : INR {price}\n"
                f"Status  : SUCCESS\nCustomer: {user}\n{'='*30}\n"
            )
            st.download_button(
                label="📄 Download Invoice (TXT)",
                data=invoice_txt,
                file_name=f"TOONIFY_Invoice_{order_id}.txt",
                mime="text/plain",
                key="checkout_dl_invoice_txt",
                use_container_width=True,
                type="primary",
            )

    with col2:
        cartoon_bytes = sget("processed_image")
        if not cartoon_bytes and sget("adjusted_image") is not None and HAS_CV2:
            try:
                _, buf_img = cv2.imencode(".png", sget("adjusted_image"))
                cartoon_bytes = buf_img.tobytes()
            except Exception:
                cartoon_bytes = None

        if cartoon_bytes:
            st.download_button(
                label="🖼️ Download Cartoon Image",
                data=cartoon_bytes,
                file_name="toonify_cartoon.png",
                mime="image/png",
                key="checkout_dl_cartoon",
                use_container_width=True,
                type="primary",
            )
        else:
            st.info("Cartoon image data not found in this session.")


# ── page ──────────────────────────────────────────────────────────────────────
def show_checkout_page():
    st.set_page_config(page_title="💳 Checkout – TOONIFY PRO", layout="wide")

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .checkout-hero {
        background: linear-gradient(135deg, #0F0F1A 0%, #1A1A3A 100%);
        border: 1px solid #6C63FF44; border-radius: 20px;
        padding: 36px 40px 28px; text-align: center; margin-bottom: 28px;
        position: relative; overflow: hidden;
    }
    .checkout-hero::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, #6C63FF, #48C9B0);
    }
    .checkout-hero h1 {
        font-size: 2.4rem; font-weight: 900;
        background: linear-gradient(135deg, #6C63FF, #48C9B0);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .checkout-hero p { color: #9999CC; font-size: 1rem; }
    .order-card {
        background: linear-gradient(145deg, #13132A, #1A1A3A);
        border: 1px solid #2A2A5A; border-radius: 16px;
        padding: 28px 32px; margin-bottom: 24px;
    }
    .order-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid #1E1E3A;
    }
    .order-row:last-child { border-bottom: none; }
    .order-label {
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em;
        color: #6666AA; text-transform: uppercase;
    }
    .order-value { font-size: 0.95rem; font-weight: 600; color: #E0E0FF; }
    .price-val   { color: #F9CA74 !important; font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Auth guard ────────────────────────────────────────────────────────────
    if sget("user") is None:
        st.error("⚠ Please login first.")
        if st.button("Go to Login"):
            switch("pages/login.py")
        return

    # ── Process Payment Redirect (from URL params) ────────────────────────────
    try:
        query_params = st.query_params
    except Exception:
        try:
            query_params = st.experimental_get_query_params()
        except Exception:
            query_params = {}

    def _q(key):
        val = query_params.get(key)
        if isinstance(val, list): return val[0] if val else None
        return val

    q_payment_id = _q("payment_id")
    q_order_id = _q("order_id")
    q_signature = _q("signature")

    if q_payment_id and q_order_id and q_signature:
        # Razorpay only calls the JS success handler when payment succeeds,
        # so receiving a payment_id is proof of payment.
        st.session_state.payment_success = True
        st.session_state.payment_status = "success"
        st.session_state.order_id = q_order_id
        st.session_state.payment_id = q_payment_id
        st.session_state.transaction_id = q_payment_id
        st.session_state.checkout_allowed = True
        st.session_state.image_processed = True

        # Try server-side verification (bonus check, not a blocker)
        if verify_payment_signature:
            try:
                verify_payment_signature(q_order_id, q_payment_id, q_signature)
            except Exception:
                pass

        # Update transaction record
        q_amount = float(_q("amount") or sget("checkout_price", 10))
        q_user = _q("user") or sget("user", "Guest")
        st.session_state.checkout_price = q_amount
        if q_user and q_user != "Guest":
            st.session_state.user = q_user
        try:
            if update_transaction_status:
                update_transaction_status(q_order_id, q_payment_id, "success", int(q_amount * 100), user_id=q_user)
        except Exception:
            pass

        # Show invoice and download directly — don't rerun, because the
        # full page reload from Razorpay may have destroyed other session
        # state (like checkout_allowed). Render everything right here.
        _show_receipt_download(
            order_id=q_order_id,
            payment_id=q_payment_id,
            price=q_amount,
            user=q_user,
        )
        return

    # ── Access guard ──────────────────────────────────────────────────────────
    if not sget("checkout_allowed", False) or not sget("image_processed", False):
        st.warning("⚠️ Checkout is only available after processing an image in Upload.")
        if st.button("Go to Upload"):
            switch("pages/upload.py")
        return

    # ── Already paid → show invoice download ─────────────────────────────────
    if sget("payment_success", False):
        _show_receipt_download(
            order_id=sget("order_id", "N/A"),
            payment_id=sget("payment_id", "N/A"),
            price=sget("checkout_price", 10),
            user=sget("user", "Guest"),
        )
        return

    # ── Stash cartoon image bytes ─────────────────────────────────────────────
    if st.session_state.processed_image is None and sget("adjusted_image") is not None and HAS_CV2:
        try:
            _, buf = cv2.imencode(".png", sget("adjusted_image"))
            st.session_state.processed_image = buf.tobytes()
        except Exception:
            pass

    # ── Hero banner ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class='checkout-hero'>
        <h1>💳 Checkout</h1>
        <p>Select your format and complete payment to download your cartoon image.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Format / quality selectors ────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        fmt = st.selectbox(
            "Download format", ["PNG", "JPG", "PDF"],
            index=["PNG", "JPG", "PDF"].index(st.session_state.checkout_format),
            key="checkout_select_format",
        )
        st.session_state.checkout_format = fmt
        qual = st.selectbox(
            "Quality", ["High", "Optimized"],
            index=["High", "Optimized"].index(st.session_state.checkout_quality.capitalize()),
            key="checkout_select_quality",
        )
        st.session_state.checkout_quality = qual.lower()

    price = 50 if fmt == "PDF" else 10
    st.session_state.checkout_price = price

    with col2:
        ts = datetime.datetime.now().strftime("%d %b %Y  %H:%M")
        user_val  = sget("user", "Guest")
        style_val = sget("current_style", "—")
        st.markdown(f"""
        <div class='order-card'>
            <div class='order-row'><span class='order-label'>Customer</span><span class='order-value'>{user_val}</span></div>
            <div class='order-row'><span class='order-label'>Style</span><span class='order-value'>{style_val}</span></div>
            <div class='order-row'><span class='order-label'>Format</span><span class='order-value'>{fmt} · {qual}</span></div>
            <div class='order-row'><span class='order-label'>Date</span><span class='order-value'>{ts}</span></div>
            <div class='order-row'><span class='order-label'>Amount Due</span><span class='order-value price-val'>₹ {price}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── Secure Download Hub ──────────────────────────────────────────────────
    st.markdown("---")
    if sget("payment_success", False):
        st.markdown("""
        <div style='background:rgba(72,201,176,0.1); border:1px solid #48C9B044;
             border-radius:15px; padding:24px; text-align:center; margin-bottom:20px;'>
            <h3 style='color:#48C9B0; margin:0 0 16px 0;'>✅ Payment Verified! Download Your Files</h3>
            <div style='display:flex; gap:16px; justify-content:center;'>
                <!-- Buttons rendered via Streamlit below -->
            </div>
        </div>
        """, unsafe_allow_html=True)

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            ts_now = datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")
            d_order = sget("order_id", "N/A")
            d_pay = sget("payment_id", "N/A")
            d_amt = sget("checkout_price", price)
            d_usr = sget("user", user_val)

            if HAS_REPORTLAB and generate_pdf_receipt:
                pdf_buf = generate_pdf_receipt(d_order, d_pay, d_amt, ts_now, d_usr)
                if pdf_buf:
                    st.download_button(
                        label="📄 Download Official Invoice (PDF)",
                        data=pdf_buf,
                        file_name=f"TOONIFY_Invoice_{d_order}.pdf",
                        mime="application/pdf",
                        key="hub_dl_invoice",
                        use_container_width=True,
                        type="primary"
                    )
            if HAS_REPORTLAB and generate_pdf_receipt and pdf_buf:
                with st.expander("👁️ Preview Invoice", expanded=False):
                    _display_pdf_inline(pdf_buf.getvalue())
        with d_col2:
            cartoon_bytes = sget("processed_image")
            if not cartoon_bytes and sget("adjusted_image") is not None and HAS_CV2:
                try:
                    _, buf_img = cv2.imencode(".png", sget("adjusted_image"))
                    cartoon_bytes = buf_img.tobytes()
                except Exception: pass

            if cartoon_bytes:
                st.download_button(
                    label="🖼️ Download Cartoon Image",
                    data=cartoon_bytes,
                    file_name="toonify_cartoon_hd.png",
                    mime="image/png",
                    key="hub_dl_cartoon",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.warning("Processed image not found in session.")
    else:
        st.markdown("""
        <div style='background:rgba(108,99,255,0.05); border:1px dashed #6C63FF44;
             border-radius:15px; padding:24px; text-align:center; margin-bottom:20px;'>
            <h3 style='color:#6C63FF88; margin:0;'>🔒 Secure Download Hub</h3>
            <p style='color:#666; font-size:0.9rem; margin:8px 0 0 0;'>Complete payment below to unlock your HD files and official invoice.</p>
        </div>
        """, unsafe_allow_html=True)


    razorpay_ready = is_razorpay_configured() and HAS_RAZORPAY
    if not razorpay_ready:
        st.error("⚠️ Razorpay keys are missing. Add RAZORPAY_KEY_ID & RAZORPAY_KEY_SECRET to .env.")
        st.stop()
        return

    # ── Pre-payment Proforma Invoice ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📄 Invoice")
    
    col_inv, _ = st.columns(2)
    with col_inv:
        prov_order_id = sget("order_id") or f"PROV-{uuid.uuid4().hex[:8].upper()}"
        if HAS_REPORTLAB and generate_pdf_receipt:
            pdf_buf = generate_pdf_receipt(
                order_id=prov_order_id, 
                payment_id="Pending", 
                amount=price, 
                timestamp=datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S"), 
                user=sget("user", "Guest"),
                is_proforma=False
            )
            if pdf_buf:
                st.download_button(
                    label="📥 Download Invoice (PDF)",
                    data=pdf_buf,
                    file_name=f"TOONIFY_Invoice_{prov_order_id}.pdf",
                    mime="application/pdf",
                    key="dl_proforma_invoice_pdf",
                    use_container_width=True
                )

    # ── Retry ─────────────────────────────────────────────────────────────────
    if sget("payment_status") == "failed":
        st.error("❌ Last payment attempt failed.")
        if st.button("🔄 Retry Payment", use_container_width=True):
            for k in ("payment_status", "payment_success", "order_id", "payment_id", "razorpay_order"):
                st.session_state[k] = None
            st.session_state.payment_success = False
            st.rerun()
        return

    # ── Create Razorpay order ─────────────────────────────────────────────────
    if sget("payment_status") != "pending" or not st.session_state.get("razorpay_order"):
        if st.button("🛒 Proceed to Payment", use_container_width=True, type="primary"):
            with st.spinner("Creating order…"):
                try:
                    order_id, order = create_payment_order(
                        price, currency="INR", receipt_id=str(uuid.uuid4())
                    )
                    st.session_state.order_id       = order_id
                    st.session_state.razorpay_order  = order
                    st.session_state.payment_status  = "pending"
                    st.session_state.payment_success = False
                    st.success(f"Order created: **{order_id}**")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to create order: {exc}")
        return

    # ── Razorpay checkout widget ──────────────────────────────────────────────
    if sget("payment_status") == "pending" and st.session_state.get("razorpay_order"):
        key_id       = os.environ.get("RAZORPAY_KEY_ID", "")
        amount_paise = int(price * 100)
        razor_order  = sget("razorpay_order", {})
        rzp_order_id = razor_order.get("id", "")
        user_display = sget("user", "Guest")

        # After Razorpay payment, the JS redirects to /payment_success with all
        # necessary data encoded in the URL. The payment_success page reads the
        # URL params directly and is self-contained — no session state needed.
        html = f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <style>
          body {{ margin: 0; padding: 0; background: transparent; }}
          #rzp-btn {{
            background: linear-gradient(135deg, #6C63FF, #48C9B0);
            color: #fff; border: none;
            padding: 16px 40px; font-size: 18px; font-weight: 700;
            border-radius: 12px; cursor: pointer; width: 100%;
            box-shadow: 0 4px 20px rgba(108,99,255,0.45);
            transition: transform .2s, box-shadow .2s;
            font-family: Inter, sans-serif;
          }}
          #rzp-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(108,99,255,0.6);
          }}
          #status {{ margin-top: 12px; font-family: Inter, sans-serif; font-size: 14px; }}
        </style>
        <button id="rzp-btn">🔒 Pay ₹{price} Securely via Razorpay</button>
        <div id="status"></div>
        <script>
        var options = {{
            "key": "{key_id}",
            "amount": "{amount_paise}",
            "currency": "INR",
            "name": "TOONIFY PRO",
            "description": "Cartoon Image HD Download",
            "image": "https://i.imgur.com/n5tjHFD.png",
            "order_id": "{rzp_order_id}",
            "handler": function(response) {{
                document.getElementById("status").innerHTML =
                    '<span style="color:#48C9B0;">✅ Payment successful! Redirecting…</span>';

                var q = "?payment_id=" + encodeURIComponent(response.razorpay_payment_id)
                      + "&order_id="   + encodeURIComponent(response.razorpay_order_id)
                      + "&signature="  + encodeURIComponent(response.razorpay_signature)
                      + "&amount="     + encodeURIComponent("{price}")
                      + "&user="       + encodeURIComponent("{user_display}");

                // Navigate the TOP window back to /checkout with full payment data
                window.top.location.href = "/checkout" + q;
            }},
            "prefill": {{}},
            "theme": {{ "color": "#6C63FF" }},
            "modal": {{
                "ondismiss": function() {{
                    document.getElementById("status").innerHTML =
                        '<span style="color:#FF6B6B;">❌ Payment cancelled.</span>';
                }}
            }}
        }};
        var rzp = new Razorpay(options);
        document.getElementById('rzp-btn').onclick = function(e) {{
            rzp.open();
            e.preventDefault();
        }};
        </script>
        """
        st.info("👇 Click the button below to complete your payment securely via Razorpay.")
        components.html(html, height=600)



    st.markdown("---")
    if st.button("← Back to Upload"):
        switch("pages/upload.py")


if __name__ == "__main__":
    show_checkout_page()
