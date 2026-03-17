import os
import io
import time
from datetime import datetime, timedelta

import streamlit as st
from PIL import Image

from style import load_css, render_sidebar
from payment_gateway import (
    verify_transaction,
    get_transaction,
    get_transaction_history,
)
from download_module import (
    prepare_image_for_download,
    create_download_token,
    validate_download_token,
    cleanup_expired_tokens,
    log_download_activity,
    generate_comparison_image,
    generate_receipt_pdf,
    get_download_history,
)


def session_state_get(key, default=None):
    if hasattr(st.session_state, "get"):
        try:
            return st.session_state.get(key, default)
        except Exception:
            pass
    try:
        return st.session_state[key] if key in st.session_state else default
    except Exception:
        return default


def _ensure_download_limits():
    now = time.time()
    recent = session_state_get("download_timestamps", [])
    recent = [t for t in recent if now - t < 60]
    session_state_get("download_timestamps")
    st.session_state["download_timestamps"] = recent
    if len(recent) >= 5:
        return False
    recent.append(now)
    st.session_state["download_timestamps"] = recent
    return True


def _to_pil(image_obj):
    import numpy as np

    if image_obj is None:
        return None
    if isinstance(image_obj, Image.Image):
        return image_obj
    if isinstance(image_obj, bytes):
        try:
            return Image.open(io.BytesIO(image_obj))
        except Exception:
            return None
    if hasattr(image_obj, "shape") and isinstance(image_obj, np.ndarray):
        return Image.fromarray(image_obj[:, :, ::-1] if image_obj.shape[2] == 3 else image_obj)
    return None


def main():
    st.set_page_config(page_title="🛡️ Secure Download", layout="wide")

    load_css()
    render_sidebar(session_state_get("user"))

    st.markdown("<h1 style='text-align:center;'>🛡️ Secure Post-Payment Download</h1>", unsafe_allow_html=True)

    if not session_state_get("user"):
        st.error("Please login first")
        st.stop()

    user_id = session_state_get("user_id") or session_state_get("user")

    order_id = session_state_get("order_id")
    payment_id = session_state_get("payment_id")

    if not order_id or not payment_id:
        st.warning("No payment in progress found. Complete checkout first.")
        st.stop()

    transaction = get_transaction(user_id, order_id)
    if not transaction:
        st.warning("No transaction found for this order. Complete payment first.")
        st.stop()

    if transaction.get("status") != "success":
        st.error("Payment not verified. Please complete checkout and wait for success.")
        st.stop()

    st.success("Payment verified. You can download your cartoon image now.")
    st.write(f"Transaction ID: {transaction.get('payment_id')}")
    st.write(f"Order ID: {transaction.get('order_id')}")
    st.write(f"Amount: ₹{transaction.get('amount', 0) / 100:.2f}")
    st.write(f"Payment time: {transaction.get('timestamp')}")

    image_obj = session_state_get("processed_image")
    original_obj = session_state_get("uploaded_image")

    if image_obj is None:
        st.error("No processed image available. Return to Upload and cartoonify image first.")
        st.stop()

    processed_pil = _to_pil(image_obj)
    original_pil = _to_pil(original_obj) if original_obj is not None else None

    # remove watermark after payment by forcing premium in out path
    st.markdown("### 📦 Download Options")

    fmt = st.selectbox("Select format", ["PNG", "JPG", "PDF"], index=0, key="download_select_format")
    quality = st.selectbox("Select quality", ["high", "optimized"], index=0, key="download_select_quality")

    own_download_path = None
    if st.button("Generate Secure Temporary Download Link"):
        # ensure a fresh local file is generated (no watermark)
        result = prepare_image_for_download(
            processed_pil,
            user_id=user_id,
            image_id=session_state_get("image_id", 0),
            style=session_state_get("current_style", "Unknown"),
            original_filename=session_state_get("uploaded_filename", "cartoon.png"),
            format_type=fmt,
            quality_mode=quality,
            is_premium_user=True,
        )
        if result.get("success"):
            out_path = result.get("path")
            token = create_download_token(
                user_id=user_id,
                transaction_id=transaction.get("id"),
                file_path=out_path,
                format_type=fmt,
                ttl_seconds=3600,
            )
            st.success("Temporary download token generated")
            st.code(token)
            st.write("Token expires in 1 hour and is valid for one download.")
            st.download_button(
                "Download now",
                data=open(out_path, "rb").read(),
                file_name=os.path.basename(out_path),
                mime="application/octet-stream",
                key=f"direct_{token}",
            )
            own_download_path = out_path
        else:
            st.error(f"Could not prepare download: {result.get('error')}")

    token_input = st.text_input("Or enter a temporary token to redeem:")
    if st.button("Redeem token") and token_input:
        valid, info = validate_download_token(token_input.strip(), user_id=user_id)
        if not valid:
            st.error(info)
        else:
            payload = info
            file_path = payload.get("file_path")
            if os.path.exists(file_path):
                if not _ensure_download_limits():
                    st.warning("Rate limit exceeded: max 5 downloads per minute.")
                else:
                    log_download_activity(user_id, transaction.get("id"), payload.get("format_type"), ip_address=None)
                    with open(file_path, "rb") as f:
                        st.download_button(
                            "Download file with token",
                            f.read(),
                            file_name=os.path.basename(file_path),
                            mime="application/octet-stream",
                            key=f"token_dl_{token_input}",
                        )
            else:
                st.error("Secure file missing; please regenerate the token.")

    st.markdown("### 🖼️ Comparison Image")
    if original_pil is not None:
        if st.button("Generate Comparison Image"):
            out_cmp = os.path.join(
                "output", "downloads", f"cmp_{user_id}_{int(datetime.now().timestamp())}.png"
            )
            os.makedirs(os.path.dirname(out_cmp), exist_ok=True)
            generate_comparison_image(original_pil, processed_pil, out_cmp)
            st.image(out_cmp, caption="Original vs Cartoon")
            st.download_button(
                "Download Comparison Image",
                open(out_cmp, "rb").read(),
                file_name=os.path.basename(out_cmp),
                mime="image/png",
                key=f"cmp_{out_cmp}",
            )

    st.markdown("### 🧾 Transaction Receipt")
    if st.button("Generate Receipt"):
        out_receipt = os.path.join(
            "output", "downloads", f"receipt_{user_id}_{int(datetime.now().timestamp())}.pdf"
        )
        os.makedirs(os.path.dirname(out_receipt), exist_ok=True)
        generate_receipt_pdf(user_id, transaction.get("id"), order_id, transaction.get("amount", 0), out_receipt)
        st.download_button(
            "Download Receipt PDF",
            open(out_receipt, "rb").read(),
            file_name=os.path.basename(out_receipt),
            mime="application/pdf",
            key=f"receipt_{out_receipt}",
        )

    st.markdown("### 📜 Download History")
    history = get_download_history(user_id)
    if history:
        st.table(history)
    else:
        st.info("No download history yet.")

    st.markdown("### 🔁 Re-download Previously Purchased Images")
    recent_tx = get_transaction_history(user_id, limit=50)
    cutoff = datetime.now() - timedelta(days=30)

    for tx in recent_tx:
        tx_time = datetime.fromisoformat(tx.get("timestamp")) if tx.get("timestamp") else None
        if tx.get("status") == "success" and tx_time and tx_time > cutoff:
            st.write(f"Order {tx.get('order_id')}, Payment {tx.get('payment_id')}, Date {tx.get('timestamp')}")
            if st.button(f"Re-download image for order {tx.get('order_id')}", key=f"redl_{tx.get('id')}"):
                # simulate re-download path if prior data exists in image_history
                st.info("To re-download, return to Upload > Cartoonify and use the Download button; this is a demo fallback.")

    cleanup_expired_tokens()



