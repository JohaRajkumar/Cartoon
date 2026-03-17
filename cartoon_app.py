import io
from typing import Optional

import cv2
import numpy as np
import streamlit as st

# import the helper effects implementations
try:
    from effects import (
        cartoonify_classic,
        pencil_sketch,
        pencil_color,
        oil_painting_effect,
        vintage_sepia_effect,
        sharpen_effect,
        adjust_brightness,
        adjust_contrast,
        adjust_saturation,
        apply_blur,
    )
except ImportError:
    # if effects.py is not available the import will fail; stub functions
    cartoonify_classic = pencil_sketch = pencil_color = None
    oil_painting_effect = vintage_sepia_effect = sharpen_effect = None
    adjust_brightness = adjust_contrast = adjust_saturation = apply_blur = None

try:
    from comparison import blend_slider, drag_reveal_slider
except ImportError:
    blend_slider = drag_reveal_slider = None


# ---------------------------------------------------------------------------
# utility helpers
# ---------------------------------------------------------------------------

def _image_to_bytes(img: np.ndarray) -> bytes:
    """Encode a BGR OpenCV image to PNG bytes."""
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()


def _combine_side_by_side(img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
    """Return a new image containing img1 and img2 horizontally concatenated.

    Both inputs are assumed to be BGR; they will be resized to the same
    height before concatenation.  If anything goes wrong we fall back to
    returning a copy of the first image.
    """
    try:
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        # scale second image to match height of first
        if h1 != h2:
            ratio = h1 / h2
            img2 = cv2.resize(img2, (int(w2 * ratio), h1), interpolation=cv2.INTER_AREA)
        combined = np.hstack([img1, img2])
        return combined
    except Exception:
        return img1.copy()


def apply_style(image: np.ndarray, style: str) -> Optional[np.ndarray]:
    """Apply the selected style to an image.

    Parameters
    ----------
    image : np.ndarray
        Input BGR image
    style : str
        Style name

    Returns
    -------
    np.ndarray or None
        Styled image or None if error
    """
    if image is None:
        return None

    if style == "Classic Cartoon":
        return cartoonify_classic(image)
    elif style == "Sketch":
        return pencil_sketch(image)
    elif style == "Pencil Color":
        return pencil_color(image)
    elif style == "Oil Painting":
        return oil_painting_effect(image, size=9)
    elif style == "Vintage/Sepia":
        return vintage_sepia_effect(image, intensity=0.7)
    elif style == "Sharpen":
        return sharpen_effect(image, strength=1.0)
    else:
        return None


# ---------------------------------------------------------------------------
# Streamlit app
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Cartoonify Image App", layout="wide")

    st.title("🖼️ Enhanced Cartoonify Image App")

    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "processed_image" not in st.session_state:
        st.session_state.processed_image = None
    if "adjusted_image" not in st.session_state:
        st.session_state.adjusted_image = None

    # ------------------------------------------------------------------
    # upload section
    # ------------------------------------------------------------------
    uploaded = st.file_uploader("Upload a photo", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        # read only once and store
        data = uploaded.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            st.session_state.uploaded_image = img
            st.session_state.processed_image = None
            st.session_state.adjusted_image = None
        else:
            st.error("Unable to decode uploaded image. Please try a different file.")

    # display original image if available
    if st.session_state.uploaded_image is not None:
        st.subheader("🖼️ Original")
        st.image(st.session_state.uploaded_image, channels="BGR", caption="Uploaded image")

    # ------------------------------------------------------------------
    # style selector and process button
    # ------------------------------------------------------------------
    st.subheader("⚙️ Style & Effects")

    col_style, col_btn = st.columns([3, 1])

    with col_style:
        style = st.radio(
            "Choose a style",
            [
                "Classic Cartoon",
                "Sketch",
                "Pencil Color",
                "Oil Painting",
                "Vintage/Sepia",
                "Sharpen",
            ],
            index=0,
            horizontal=True,
            help=(
                "Classic Cartoon: smooth colors, bold outlines.\n"
                "Sketch: pencil-like monochrome drawing.\n"
                "Pencil Color: soft colored pencil effect.\n"
                "Oil Painting: smooth, painterly effect.\n"
                "Vintage/Sepia: aged, nostalgic look.\n"
                "Sharpen: enhanced details and edges."
            ),
        )

    with col_btn:
        st.write("")  # spacing
        process_btn = st.button("✨ Process Image", use_container_width=True)

    if process_btn and st.session_state.uploaded_image is not None:
        with st.spinner("Processing image..."):
            img = st.session_state.uploaded_image
            st.session_state.processed_image = apply_style(img, style)
            st.session_state.adjusted_image = None

    # ------------------------------------------------------------------
    # adjustable controls
    # ------------------------------------------------------------------
    if st.session_state.processed_image is not None:
        st.subheader("🎨 Adjustment Controls")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            brightness = st.slider("Brightness", 0.5, 2.0, 1.0, step=0.1)

        with col2:
            contrast = st.slider("Contrast", 0.5, 2.0, 1.0, step=0.1)

        with col3:
            saturation = st.slider("Color Intensity", 0.5, 2.0, 1.0, step=0.1)

        with col4:
            blur_strength = st.slider("Blur Strength", 1.0, 15.0, 1.0, step=0.5)

        # apply adjustments
        adjusted = st.session_state.processed_image.copy()

        if brightness != 1.0:
            adjusted = adjust_brightness(adjusted, brightness)

        if contrast != 1.0:
            adjusted = adjust_contrast(adjusted, contrast)

        if saturation != 1.0:
            adjusted = adjust_saturation(adjusted, saturation)

        if blur_strength > 1.0:
            adjusted = apply_blur(adjusted, blur_strength)

        st.session_state.adjusted_image = adjusted

    # ------------------------------------------------------------------
    # comparison modes
    # ------------------------------------------------------------------
    if st.session_state.adjusted_image is not None:
        st.markdown("---")
        st.subheader("📊 Comparison Modes")

        comp_mode = st.radio(
            "Select comparison view",
            ["Blend Slider", "Drag Reveal", "Side-by-Side"],
            horizontal=True,
        )

        if comp_mode == "Blend Slider":
            blend_slider(
                st.session_state.uploaded_image,
                st.session_state.adjusted_image,
                key="blend_main",
            )

        elif comp_mode == "Drag Reveal":
            drag_reveal_slider(
                st.session_state.uploaded_image,
                st.session_state.adjusted_image,
                key="drag_main",
            )

        elif comp_mode == "Side-by-Side":
            zoom = st.slider("Zoom preview", 1.0, 3.0, 1.0, step=0.1)
            col1, col2 = st.columns(2)

            with col1:
                w = int(st.session_state.uploaded_image.shape[1] * zoom)
                st.image(
                    st.session_state.uploaded_image,
                    channels="BGR",
                    caption="Original",
                    width=w,
                )
                st.caption("Original image")

            with col2:
                w = int(st.session_state.adjusted_image.shape[1] * zoom)
                st.image(
                    st.session_state.adjusted_image,
                    channels="BGR",
                    caption="Processed",
                    width=w,
                )
                st.caption(f"{style} result")

        # ------------------------------------------------------------------
        # download button
        # ------------------------------------------------------------------
        st.markdown("---")

        col_dl, col_reset = st.columns([1, 1])

        with col_dl:
            combined = _combine_side_by_side(
                st.session_state.uploaded_image, st.session_state.adjusted_image
            )
            buf = _image_to_bytes(combined)
            st.download_button(
                "⬇️ Download Preview",
                data=buf,
                file_name="cartoon_preview.png",
                mime="image/png",
                use_container_width=True,
            )

        with col_reset:
            if st.button("🔄 Try Another Style", use_container_width=True):
                st.session_state.processed_image = None
                st.session_state.adjusted_image = None
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
                else:
                    import uuid
                    st.experimental_set_query_params(_r=uuid.uuid4().hex)


if __name__ == "__main__":
    main()
