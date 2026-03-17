import streamlit as st
import streamlit.components.v1 as components
import streamlit.runtime.state.session_state_proxy as ssp
import sys
import os
import io
from PIL import Image
import uuid
from datetime import datetime
import cv2
import numpy as np
from typing import Optional


def set_state(key, value):
    """Safely assign to Streamlit session state in both runtime and bare/test modes."""
    if hasattr(st, "runtime") and not st.runtime.exists():
        try:
            ssp._mock_session_state._state._new_session_state[key] = value
            return
        except Exception:
            pass
    try:
        st.session_state[key] = value
    except Exception:
        # fall back for any edge cases where direct set fails
        try:
            if hasattr(ssp, "_mock_session_state"):
                ssp._mock_session_state._state._new_session_state[key] = value
        except Exception:
            pass


def safe_switch_page(target):
    """Try both path and name for st.switch_page to avoid missing page errors."""
    if not hasattr(st, "switch_page"):
        return False
    try:
        st.switch_page(target)
        return True
    except Exception:
        pass
    try:
        if target.startswith("pages/") and target.endswith(".py"):
            st.switch_page(target.split("/")[-1][:-3])
            return True
        if target.endswith(".py"):
            st.switch_page(target[:-3])
            return True
        st.switch_page(target.replace("_", " ").title())
        return True
    except Exception:
        return False


def session_state_get(key, default=None):
    """Safely get a value from Streamlit session state in runtime and bare/test modes."""
    if hasattr(st.session_state, "get"):
        try:
            return st.session_state.get(key, default)
        except Exception:
            pass
    try:
        return st.session_state[key] if key in st.session_state else default
    except Exception:
        return default


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
            if not safe_switch_page(target):
                st.warning("Navigation failed. Please use the sidebar links.")


render_custom_sidebar()


# ---------- IMAGE SIZE HELPERS ----------

def _limit_numpy_image(img: np.ndarray, maxw: int = 600, maxh: int = 600) -> np.ndarray:
    """Return a resized copy of a BGR numpy image if it's too large.

    Maintains aspect ratio and constrains both width and height.
    """
    if img is None:
        return img
    h, w = img.shape[:2]
    if w > maxw or h > maxh:
        ratio = min(maxw / w, maxh / h)
        return cv2.resize(img, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)
    return img


def _limit_pil_image(pil_img: Image.Image, maxw: int = 600, maxh: int = 600) -> Image.Image:
    """Return a resized copy of a PIL image if it's too large.

    Uses the modern ``Resampling`` enum where available to avoid
    ``ANTIALIAS`` deprecation errors in recent Pillow releases.
    """
    if pil_img is None:
        return pil_img
    w, h = pil_img.size
    if w > maxw or h > maxh:
        ratio = min(maxw / w, maxh / h)
        resample = getattr(Image, "Resampling", Image).LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
        return pil_img.resize((int(w * ratio), int(h * ratio)), resample)
    return pil_img


# Import new effects and comparison tools
try:
    from effects import (
        oil_painting_effect,
        vintage_sepia_effect,
        sharpen_effect,
        adjust_brightness,
        adjust_contrast,
        adjust_saturation,
        apply_blur,
    )
except ImportError:
    oil_painting_effect = vintage_sepia_effect = sharpen_effect = None
    adjust_brightness = adjust_contrast = adjust_saturation = apply_blur = None

try:
    from comparison import blend_slider, drag_reveal_slider
except ImportError:
    blend_slider = drag_reveal_slider = None


# ---------- HELPERS ----------

def decode_image_bytes(raw_bytes: bytes) -> "Optional[np.ndarray]":
    """Convert raw file bytes to a BGR OpenCV image.

    This helper does a two‑stage attempt because OpenCV's decoder can
    silently fail on certain unusual formats (e.g. CMYK JPEGs, some
    animated GIFs, or corrupted headers).  If ``cv2.imdecode`` returns
    ``None`` we fall back to using Pillow, which handles a wider range of
    inputs; the resulting RGB image is then converted to BGR for
    consistency with the rest of the codebase.

    Returns ``None`` only if *both* decoders fail or the data is not a
    valid image at all.
    """
    if not raw_bytes:
        return None

    # first try OpenCV directly
    try:
        arr = np.asarray(bytearray(raw_bytes), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            return img
    except Exception:
        pass

    # OpenCV failed; try Pillow as a fallback
    try:
        from PIL import Image
        from io import BytesIO

        pil_img = Image.open(BytesIO(raw_bytes))
        pil_img = pil_img.convert("RGB")
        rgb = np.array(pil_img)
        # convert RGB→BGR
        return rgb[:, :, ::-1].copy()
    except Exception:
        return None

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from style import load_css, render_sidebar
from cartoonify import apply_cartoon_style

# bring in downloader and cleanup
from download_module import prepare_image_for_download, delete_old_files
# payment integration (import lazily to avoid errors when razorpay is missing)
try:
    from payment_gateway import create_payment_order, verify_payment_signature, update_transaction_status, HAS_RAZORPAY
except ImportError:
    # when razorpay isn't installed the module still exists but functions
    # will raise at runtime; we provide a flag for tests.
    create_payment_order = None  # type: ignore
    verify_payment_signature = None  # type: ignore
    update_transaction_status = None  # type: ignore
    HAS_RAZORPAY = False  # type: ignore

# ---------- SESSION INIT ----------
from registration import init_session_state, logout_user
init_session_state()

# legacy storage for images etc
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

if "cartoon_result" not in st.session_state:
    st.session_state.cartoon_result = None

if "current_style" not in st.session_state:
    st.session_state.current_style = "Classic"

if "adjusted_image" not in st.session_state:
    st.session_state.adjusted_image = None

if "processed_image" not in st.session_state:
    st.session_state.processed_image = None

# run cleanup periodically (on page load)
delete_old_files()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🎨TOONIFY PRO|Upload", page_icon="📤", layout="wide")

# ---------- LOAD CSS ----------
load_css()
st.markdown("<h2 style='text-align:center;'>🎨TOONIFY PRO</h2>", unsafe_allow_html=True)

# ---------- LOGIN CHECK ----------
if not st.session_state.logged_in or not st.session_state.user:
    st.error("⚠ Please login first")
    st.page_link("pages/login.py", label="Go to Login")
    st.stop()

# ---------- SIDEBAR ----------
render_sidebar(session_state_get("user"))

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>📤 Upload & Cartoonify</h1>", unsafe_allow_html=True)
st.write("Supported formats: JPG, JPEG, PNG, BMP | Max size: 10MB")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = ["jpg", "jpeg", "png", "bmp"]

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- FILE BROWSER ----------
uploaded_file = st.file_uploader("Choose an image...", type=ALLOWED_TYPES)

if uploaded_file is not None:

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("❌ File size exceeds 10MB limit")
    else:
        # read everything from the stream immediately; this avoids any
        # seek/verify pointer headaches and gives us raw bytes we can
        # examine regardless of how PIL behaves.
        raw_bytes = uploaded_file.read()
        if not raw_bytes:
            st.error("❌ Uploaded file contains no data; please try again.")
            st.stop()

        # decode the image (OpenCV + fallback to PIL).  we will also
        # attempt a lightweight PIL verify just to make error messages
        # more informative for the user.
        cv_image = decode_image_bytes(raw_bytes)
        if cv_image is None:
            # gather some diagnostics
            header = raw_bytes[:10]
            st.error(
                "❌ Could not read the uploaded image. "
                "Please ensure the file is a valid JPG/PNG/BMP and try again.\n"
                f"Read {len(raw_bytes)} bytes, header={header!r}."
            )
            st.stop()

        # also build a PIL image for display purposes – cv2 returns BGR and
        # doesn't carry EXIF orientation etc, so we use PIL to show the
        # same file the user uploaded.
        try:
            pil_image = Image.open(io.BytesIO(raw_bytes))
        except Exception:
            pil_image = None

        # save bytes since we need to keep the file for later pages
        ext = uploaded_file.name.split(".")[-1].lower()
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_name)
        with open(save_path, "wb") as f:
            f.write(raw_bytes)

        st.session_state.uploaded_image = cv_image
        # store the original filename for downstream use
        st.session_state.uploaded_filename = uploaded_file.name
        # store the PIL object separately so we can use it for captions, size,
        # etc.  if PIL decoding failed we just fall back to the numpy image.
        st.session_state.uploaded_pil = pil_image

        st.success("✅ Image uploaded successfully!")


        # Display original and controls
        col1, col2 = st.columns([1, 1])

        with col1:
            # prefer the PIL object for display if available
            display_img = session_state_get("uploaded_pil")
            if display_img is None:
                display_img = Image.open(io.BytesIO(raw_bytes))
            # remember the original size for reporting; the user might
            # still care about original dimensions even if we downscale
            orig_w, orig_h = display_img.size
            display_img = _limit_pil_image(display_img)
            st.image(display_img, caption="Original Image")
            size_kb = round(uploaded_file.size / 1024, 2)
            st.write(f"**File:** {uploaded_file.name}")
            st.write(f"**Dimensions:** {orig_w} × {orig_h} px")
            st.write(f"**Size:** {size_kb} KB")

        with col2:
            st.write("### 🎨 Cartoon Features")
            style = st.selectbox(
                "Cartoon Style",
                [
                    "Classic",
                    "Soft",
                    "Bold",
                    "Comic",
                    "Sketch",
                    "Watercolor",
                    "Pencil Color",
                    "Oil Painting",
                    "Vintage/Sepia",
                    "Sharpen",
                ],
                index=0,
            )
            num_colors = st.slider("Number of Colors", 2, 20, 8)
            smoothness = st.slider("Smoothness", 1, 10, 5)
            edge_method = st.selectbox(
                "Edge Method",
                ["canny", "adaptive", "gray", "sobel", "laplacian"],
                index=0,
            )
            edge_thickness = st.slider("Edge Thickness", 1, 10, 1)
            sensitivity = st.slider("Sensitivity", 0.2, 2.0, 1.0, step=0.1)

            # adjustment controls placed before apply
            st.markdown("---")
            st.write("#### Adjustments")
            brightness = st.slider("Brightness", 0.5, 2.0, 1.0, step=0.1, key="brightness_upload")
            contrast = st.slider("Contrast", 0.5, 2.0, 1.0, step=0.1, key="contrast_upload")
            saturation = st.slider("Color Intensity", 0.5, 2.0, 1.0, step=0.1, key="saturation_upload")
            blur_strength = st.slider("Blur Strength", 1.0, 15.0, 1.0, step=0.5, key="blur_upload")

            st.markdown("---")
            st.write("#### Comparison Mode")
            comp_mode = st.radio(
                "View mode",
                ["Side-by-Side", "Blend Slider", "Drag Reveal"],
                horizontal=True,
                key="comp_mode_upload",
            )

            if st.button("✨ Apply Cartoonify", key="apply_cartoon_upload"):
                with st.spinner("Processing..."):
                    if st.session_state.uploaded_image is None:
                        st.error(
                            "No image is available for processing. "
                            "This usually means the upload failed or your session expired; "
                            "please try uploading again."
                        )
                    else:
                        # Handle new styles separately
                        if style == "Oil Painting":
                            result = oil_painting_effect(st.session_state.uploaded_image, size=9) if oil_painting_effect else None
                        elif style == "Vintage/Sepia":
                            result = vintage_sepia_effect(st.session_state.uploaded_image, intensity=0.7) if vintage_sepia_effect else None
                        elif style == "Sharpen":
                            result = sharpen_effect(st.session_state.uploaded_image, strength=1.0) if sharpen_effect else None
                        else:
                            # Use standard cartoonify for built-in styles
                            result = apply_cartoon_style(
                                st.session_state.uploaded_image,
                                style=style,
                                num_colors=num_colors,
                                smoothness=smoothness,
                                edge_method=edge_method,
                                thickness=edge_thickness,
                                sensitivity=sensitivity,
                            )
                        
                        if result is not None:
                            st.session_state.cartoon_result = result
                            st.session_state.current_style = style

                            # apply adjustments immediately using slider values
                            adjusted = result.copy()
                            # read slider states (they already exist because defined above)
                            b = session_state_get("brightness_upload", 1.0)
                            c = session_state_get("contrast_upload", 1.0)
                            s = session_state_get("saturation_upload", 1.0)
                            bl = session_state_get("blur_upload", 1.0)

                            if b != 1.0 and adjust_brightness:
                                adjusted = adjust_brightness(adjusted, b)
                            if c != 1.0 and adjust_contrast:
                                adjusted = adjust_contrast(adjusted, c)
                            if s != 1.0 and adjust_saturation:
                                adjusted = adjust_saturation(adjusted, s)
                            if bl > 1.0 and apply_blur:
                                adjusted = apply_blur(adjusted, bl)

                            st.session_state.adjusted_image = adjusted
                            # Store the processed image bytes for cross-page download availability
                            try:
                                _, buf_img = cv2.imencode('.png', adjusted)
                                st.session_state.processed_image = buf_img.tobytes()
                            except Exception:
                                st.session_state.processed_image = None

                            if np.array_equal(result, st.session_state.uploaded_image):
                                st.warning("No visible change; try different settings for a stronger effect.")
                            # rerun to refresh UI
                            if hasattr(st, "experimental_rerun"):
                                st.experimental_rerun()
                            else:
                                import uuid
                                if hasattr(st, "experimental_set_query_params"):
                                    st.experimental_set_query_params(_r=uuid.uuid4().hex)
                                elif hasattr(st, "rerun"):
                                    st.rerun()
                        else:
                            st.error("Cartoonify failed. Try different settings.")




def navigate_to_checkout():
    """Programmatically open the hidden checkout page.

    Checkout is not exposed in the sidebar; it is only reachable from Upload
    after an image has been processed.
    """
    set_state("image_processed", True)
    set_state("checkout_allowed", True)
    # Ensure processed_image is set
    adjusted = session_state_get("adjusted_image")
    if adjusted is not None:
        try:
            _, buf_img = cv2.imencode('.png', adjusted)
            set_state("processed_image", buf_img.tobytes())
        except Exception:
            set_state("processed_image", None)

    # In tests or non-Streamlit runtime, avoid calling switch_page because it
    # can raise NoReturn-like errors.
    if hasattr(st, "runtime") and not st.runtime.exists():
        set_state("menu", "💳 Checkout")
        set_state("current_page", "Checkout")
        set_state("current_page_path", "pages/checkout.py")
        return

    # switch to checkout page directly
    if not safe_switch_page("pages/checkout.py"):
        # fallback for environments where switch_page may not be present;
        # set a flag and rerun for custom app routing to pick it up.
        set_state("menu", "💳 Checkout")
        set_state("current_page", "Checkout")
        set_state("current_page_path", "pages/checkout.py")
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        elif hasattr(st, "rerun"):
            st.rerun()


# ---------- DISPLAY RESULT ----------
if st.session_state.cartoon_result is not None and st.session_state.uploaded_image is not None:
    # ---------- PAYMENT STATUS FOR MAIN CONTENT ----------
    paid_key = f"paid_{session_state_get('uploaded_filename','')}_{session_state_get('current_style','')}"
    has_paid = session_state_get(paid_key, False) or session_state_get("payment_success", False)
    if session_state_get("payment_success", False) and not session_state_get(paid_key, False):
        st.session_state[paid_key] = True
        has_paid = True
    st.markdown("---")
    st.write("### 🔍 Result")

    # show result using preset comparison mode
    comp_mode = session_state_get("comp_mode_upload", "Side-by-Side")

    if comp_mode == "Side-by-Side":
        col1, col2 = st.columns(2)
        with col1:
            ori = _limit_numpy_image(st.session_state.uploaded_image)
            st.image(ori, channels="BGR", caption="Original")
        with col2:
            cart = _limit_numpy_image(st.session_state.adjusted_image)
            st.image(cart, channels="BGR", caption="Cartoonified")

    elif comp_mode == "Blend Slider" and blend_slider:
        blend_slider(
            st.session_state.uploaded_image,
            st.session_state.adjusted_image,
            key="blend_upload",
        )

    elif comp_mode == "Drag Reveal" and drag_reveal_slider:
        drag_reveal_slider(
            st.session_state.uploaded_image,
            st.session_state.adjusted_image,
            key="drag_upload",
        )

    # show unified checkout/download controls after result preview
    st.markdown("---")
    if not has_paid:
        st.warning("Please complete ₹10 payment to download the processed image.")
        if st.button("💳 Proceed to Checkout", key="result_proceed_checkout"):
            navigate_to_checkout()
    else:
        st.success("Payment successful. You can now download the image.")
        if st.session_state.adjusted_image is not None:
            _, buffer = cv2.imencode(".png", st.session_state.adjusted_image)
            st.download_button(
                label="⬇️ Download Cartoon",
                data=buffer.tobytes(),
                file_name="cartoon_image.png",
                mime="image/png",
                key="download_after_payment",
                use_container_width=True,
            )

    # Reset button remains at bottom for clarity
    st.markdown("---")
    if st.button("🔄 Try Another Style", key="reset_result", use_container_width=True):
        st.session_state.cartoon_result = None
        st.session_state.adjusted_image = None
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            import uuid
            if hasattr(st, "experimental_set_query_params"):
                st.experimental_set_query_params(_r=uuid.uuid4().hex)
            elif hasattr(st, "rerun"):
                st.rerun()

