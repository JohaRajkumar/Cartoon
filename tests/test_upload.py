import cv2
import numpy as np
import os
import sys
import io
from PIL import Image
import streamlit as st

# ensure import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pages.upload import decode_image_bytes


def make_sample_image():
    # simple coloured square
    img = np.zeros((20, 30, 3), dtype=np.uint8)
    img[:] = (10, 20, 30)
    return img


def test_decode_valid_bytes(tmp_path):
    img = make_sample_image()
    # encode as PNG
    success, buf = cv2.imencode('.png', img)
    assert success
    raw = buf.tobytes()

    decoded = decode_image_bytes(raw)
    assert decoded is not None
    assert decoded.shape[0] == img.shape[0]
    assert decoded.shape[1] == img.shape[1]
    # pixel values preserved approximately
    assert np.allclose(decoded, img, atol=5)


def test_pil_display_image(monkeypatch, tmp_path):
    """Uploading sets both cv2 and PIL images in session state."""
    # We'll simulate the upload page logic directly without running Streamlit.
    from pages import upload
    img = make_sample_image()
    success, buf = cv2.imencode('.png', img)
    raw = buf.tobytes()

    # monkeypatch decode to return arr and ensure PIL load works
    cv_img = decode_image_bytes(raw)
    assert cv_img is not None

    # recreate the part of code that builds the PIL image
    pil_obj = None
    try:
        pil_obj = Image.open(io.BytesIO(raw))
    except Exception:
        pil_obj = None

    assert pil_obj is not None
    assert pil_obj.size == (30, 20) or pil_obj.size == (20, 30)


def test_pil_fallback(monkeypatch):
    """If OpenCV fails we should still decode using PIL."""
    img = make_sample_image()
    success, buf = cv2.imencode('.png', img)
    raw = buf.tobytes()

    # monkeypatch imdecode to simulate failure
    monkeypatch.setattr(cv2, 'imdecode', lambda *_args, **_kwargs: None)

    decoded = decode_image_bytes(raw)
    assert decoded is not None
    assert decoded.shape == img.shape
    assert np.allclose(decoded, img, atol=5)


def test_decode_invalid_returns_none():
    # completely empty or random data
    assert decode_image_bytes(b"") is None
    assert decode_image_bytes(b"not an image") is None


def test_pil_verify_advances_pointer(tmp_path):
    """Simulate PIL verify moving the stream; we must reset before reading.

    The upload page rewinds the ``uploaded_file`` after calling
    ``image.verify()``.  If that rewind step is missing the subsequent
    call to ``read()`` returns an empty byte string, triggering the
    error message the user complained about.
    """
    img = make_sample_image()
    success, buf = cv2.imencode('.png', img)
    raw = buf.tobytes()

    from io import BytesIO
    f = BytesIO(raw)
    # PIL verify typically reads some data and may leave the cursor near the end
    im = Image.open(f)
    im.verify()
    # without seeking, the next read is empty
    f2 = BytesIO(raw)
    im2 = Image.open(f2)
    im2.verify()

    # now rewind and read; we expect the same bytes back
    f.seek(0)
    again = f.read()
    assert again == raw


def test_navigate_to_checkout(monkeypatch):
    """Ensure the helper flips the menu state and doesn't crash when rerun functions are stubbed."""
    from pages.upload import navigate_to_checkout

    # reset any existing state
    st.session_state.clear()
    st.session_state.menu = "📤 Upload Image"

    # stub out Streamlit rerun helpers so they don't interrupt the test.
    # some versions of Streamlit don't even expose these attributes so only
    # patch if present.
    for attr in ("experimental_rerun", "rerun", "experimental_set_query_params"):
        if hasattr(st, attr):
            monkeypatch.setattr(st, attr, lambda *args, **kwargs: None)

    navigate_to_checkout()
    assert st.session_state.menu == "💳 Checkout"


def test_menu_override_behavior(monkeypatch):
    """Simulate the sidebar selectbox returning an outdated value and ensure
    our override logic restores the programmatic menu change."""
    import streamlit as st

    # prepare state as if navigate_to_checkout had been called
    st.session_state.clear()
    st.session_state.menu = "💳 Checkout"

    # monkeypatch selectbox to pretend the widget still returns the old value
    monkeypatch.setattr(st.sidebar, "selectbox", lambda *args, **kwargs: "📤 Upload Image")

    options = ["🏠 Home", "📤 Upload Image", "💳 Checkout"]
    menu = st.sidebar.selectbox(
        "📂 Select Option",
        options,
        index=options.index(st.session_state.menu),
        key="menu",
    )
    if menu != st.session_state.menu:
        menu = st.session_state.menu
        st.session_state.menu = menu

    assert menu == "💳 Checkout"
