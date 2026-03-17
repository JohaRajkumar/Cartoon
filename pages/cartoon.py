import streamlit as st
import sys
import os
import cv2
import numpy as np

# ---------- PATH FIX ----------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from style import load_css, render_sidebar, session_state_get
from cartoonify import apply_cartoon_style

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="🎨TOONIFY PRO | Cartoonify", page_icon="🎨", layout="wide")

load_css()
st.markdown("<h1 style='text-align:center;'>🎨 TOONIFY PRO</h1>", unsafe_allow_html=True)

# ---------- SESSION SETUP ----------
if "original_image" not in st.session_state:
    st.session_state.original_image = None

# ---------- UPLOAD ----------
st.markdown("## Upload Image")
uploaded = st.file_uploader("Choose a photo", type=["png", "jpg", "jpeg"])
if uploaded is not None:
    raw = uploaded.read()
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is not None:
        st.session_state.original_image = img
        st.success("Image loaded")
        # clear previous result
        st.session_state.pop("cartoon_image", None)
    else:
        st.error("Failed to read image file")

# ---------- SETTINGS PANEL ----------
st.markdown("---")
with st.expander("🎛️ Cartoon Settings", expanded=True):
    style = st.selectbox("Cartoon Style", ["Classic", "Soft", "Bold", "Comic", "Sketch", "Watercolor", "Pencil Color"], index=0)
    num_colors = st.slider("Number of Colors", 2, 20, 8)
    smoothness = st.slider("Smoothness", 1, 10, 5)
    edge_method = st.selectbox(
        "Edge Method",
        ["canny", "adaptive", "gray", "sobel", "laplacian"],
        index=0,
    )
    edge_thickness = st.slider("Edge Thickness", 1, 10, 1)
    sensitivity = st.slider("Sensitivity", 0.2, 2.0, 1.0, step=0.1)
    apply = st.button("✨ Apply Cartoonify")

# ---------- PROCESSING ----------
if apply and st.session_state.original_image is not None:
    with st.spinner("Processing image..."):
        result = apply_cartoon_style(
            st.session_state.original_image,
            style=style,
            num_colors=num_colors,
            smoothness=smoothness,
            edge_method=edge_method,
            thickness=edge_thickness,
            sensitivity=sensitivity,
        )
        if result is not None:
            # it’s possible for a valid cartoon to look identical to the
            # source (e.g. a blank image or very subtle changes).  rather
            # than showing an error we display the output and gently notify
            # the user that nothing changed.
            st.session_state.cartoon_image = result
            if np.array_equal(result, st.session_state.original_image):
                st.warning("No visible change; try different settings for a stronger effect.")
        else:
            st.error("Cartoonify failed. Try different settings.")

# ---------- DISPLAY ----------
col1, col2 = st.columns(2)
if st.session_state.original_image is not None:
    col1.image(st.session_state.original_image, channels="BGR", caption="Original Image")
else:
    col1.write("👈 Upload an image to get started")

if "cartoon_image" in st.session_state:
    col2.image(st.session_state.cartoon_image, channels="BGR", caption="Cartoonified")
    # download button
    _, buffer = cv2.imencode(".png", st.session_state.cartoon_image)
    st.download_button(
        label="⬇️ Download Cartoon",
        data=buffer.tobytes(),
        file_name="cartoon.png",
        mime="image/png",
        key="download_cartoon",
    )
else:
    col2.write("✨ Output will appear here")

# ---------- NAVIGATION ----------
render_sidebar(session_state_get("user"))
