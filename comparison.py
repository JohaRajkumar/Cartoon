"""Reusable comparison helpers for the Cartoonify app.

This module is intentionally separate so that the blending/slider logic can
be imported into multiple pages if desired.  At the moment the main
`cartoon_app.py` script uses the ``blend_slider`` function to render a simple
interactive comparison control, but additional utilities could be added in the
future (e.g. more sophisticated "fancy slider" components or export helpers).
"""

from typing import Optional

import cv2
import numpy as np
import streamlit as st


# ---------------------------------------------------------------------------
# comparison utilities
# ---------------------------------------------------------------------------

def blend_slider(original: np.ndarray, processed: np.ndarray, key: Optional[str] = None) -> np.ndarray:
    """Display a Streamlit slider that blends the two images.

    Parameters
    ----------
    original : np.ndarray
        The source image (BGR).
    processed : np.ndarray
        The styled/processed image (BGR) of the same shape as ``original``.
    key : Optional[str]
        Optional Streamlit widget key for the slider; useful if the same
        function is called multiple times in the same app.

    Returns
    -------
    np.ndarray
        The blended image corresponding to the slider position.

    Side effects
    ------------
    Renders a slider titled ``"Blend original ↔ processed"`` and the
    blended result to the current Streamlit app.  The returned image is also
    displayed by this function.
    """
    if original is None or processed is None:
        raise ValueError("Both images must be provided for comparison")

    comp = st.slider("Blend original ↔ processed", 0.0, 1.0, 0.5, step=0.01, key=key)
    blended = cv2.addWeighted(original, 1 - comp, processed, comp, 0)
    # restrict display size to a sane maximum (e.g. 600×600px)
    maxw = min(original.shape[1], 600)
    maxh = 600
    h, w = blended.shape[:2]
    if w > maxw or h > maxh:
        ratio = min(maxw / w, maxh / h)
        blended_disp = cv2.resize(blended, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)
    else:
        blended_disp = blended
    st.image(blended_disp, channels="BGR", caption="Comparison", width=blended_disp.shape[1])
    st.caption("Use the slider to mix between original and processed image")
    return blended


def drag_reveal_slider(original: np.ndarray, processed: np.ndarray, key: Optional[str] = None) -> np.ndarray:
    """Display a drag-to-reveal slider showing processed image overlaid on original.

    This creates an interactive "reveal" effect where the slider position controls
    how much of the processed image is visible on top of the original (from left to right).

    Parameters
    ----------
    original : np.ndarray
        The source image (BGR).
    processed : np.ndarray
        The styled/processed image (BGR) of the same shape as ``original``.
    key : Optional[str]
        Optional Streamlit widget key for the slider.

    Returns
    -------
    np.ndarray
        The revealed/composite image.

    Side effects
    ------------
    Renders a slider titled ``"Drag to reveal processed ↔"`` and the
    composite image to the current Streamlit app.
    """
    if original is None or processed is None:
        raise ValueError("Both images must be provided for comparison")

    try:
        reveal = st.slider(
            "Drag to reveal processed ↔",
            0.0,
            1.0,
            0.5,
            step=0.01,
            key=key,
        )

        # get image dimensions
        h, w = original.shape[:2]

        # calculate reveal position (how many columns to show from processed)
        reveal_pos = int(w * reveal)

        # create composite: original image with processed overlay
        composite = original.copy()

        # overlay processed image from left up to reveal_pos
        if reveal_pos > 0:
            composite[:, :reveal_pos] = processed[:, :reveal_pos]

        # add a vertical line at the reveal position for visual feedback
        if 0 < reveal_pos < w:
            cv2.line(composite, (reveal_pos, 0), (reveal_pos, h), (0, 255, 0), 2)

        # constrain size to avoid enormous output (max 600×600px)
        maxw = min(original.shape[1], 600)
        maxh = 600
        h, w = composite.shape[:2]
        if w > maxw or h > maxh:
            ratio = min(maxw / w, maxh / h)
            composite_disp = cv2.resize(composite, (int(w * ratio), int(h * ratio)), interpolation=cv2.INTER_AREA)
        else:
            composite_disp = composite
        st.image(composite_disp, channels="BGR", caption="Drag Reveal Comparison", width=composite_disp.shape[1])
        st.caption("Slide left/right to gradually reveal the processed image")

        return composite
    except Exception as e:
        st.error(f"Error in drag_reveal_slider: {e}")
        return original.copy()

