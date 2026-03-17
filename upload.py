import streamlit as st
import cv2
import numpy as np
import os
import uuid
from PIL import Image

from classic_cartoon import apply_classic_cartoon

def show_upload_page():

    st.title("🎨 Cartoon Image Generator")

    uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:

        # read bytes once and save to uploads folder
        raw_bytes = uploaded_file.read()
        file_bytes = np.asarray(bytearray(raw_bytes), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)

        # ensure uploads dir exists
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # save to disk so other pages can access by path
        filename = f"upload_{uuid.uuid4().hex}.png"
        saved_path = os.path.join(uploads_dir, filename)
        with open(saved_path, "wb") as f:
            f.write(raw_bytes)

        st.success("✅ Image uploaded successfully!")

        # store path in session so pages/cartoon.py can access it
        st.session_state.uploaded_image_path = saved_path

        st.image(image, caption="🖼️ Original Image", width='stretch')

        st.markdown("---")
        st.markdown("## 🎨 Apply Classic Cartoon Effect")

        # 🔥 Only ONE control
        intensity = st.selectbox(
            "Select Cartoon Intensity",
            ["Light", "Medium", "Strong"]
        )

        if st.button("✨ Apply Cartoonify"):

            # 🎯 Map intensity → settings internally
            if intensity == "Light":
                num_colors = 12
                smoothness = 3

            elif intensity == "Medium":
                num_colors = 8
                smoothness = 5

            else:  # Strong
                num_colors = 4
                smoothness = 7

            # Convert to cartoon
            cartoon = apply_classic_cartoon(
                image,
                num_colors=num_colors,
                smoothness=smoothness
            )

            st.markdown("### 🔍 Before vs After")

            col1, col2 = st.columns(2)

            with col1:
                st.image(image, caption="🖼️ Original", width='stretch')

            with col2:
                st.image(cartoon, caption="🎨 Cartoon", width='stretch')

        # allow navigating to the full Cartoonify page which expects a saved path
        if st.button("Open Cartoonify Page"):
            st.success("Opening Cartoonify page...")
            st.switch_page("pages/cartoon.py")