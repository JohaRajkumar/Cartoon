"""cartoonify.py

Simple cartoonify pipeline for Streamlit app.

Functions:
- apply_cartoon(image): returns BGR cartoonified image or None

Pipeline implemented:
- repeated bilateral filtering to smooth colors
- optional color quantization via k-means (fallback to pyramid mean shift)
- combine with edge mask to create cartoon effect
"""

from typing import Optional

try:
    import cv2
except Exception:
    cv2 = None

import numpy as np

# import helper modules from project
from cartoon_filter import apply_bilateral_filter, color_quantization
from edge_detection import detect_edges

# import effects module (pencil/sketch effects)
try:
    from effects import sketch_effect, pencil_color_effect
except ImportError:
    sketch_effect = None
    pencil_color_effect = None


def _ensure_cv2():
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) is required. Install with `pip install opencv-python`")


def _combine_color_edges(color_img: np.ndarray, edges: np.ndarray) -> Optional[np.ndarray]:
    """Overlay binary edge mask onto color image, producing cartoon effect.

    `edges` should be single-channel binary (255=edges). The function inverts
    them so that black lines appear on top of the color image.
    """
    _ensure_cv2()
    if color_img is None or edges is None:
        return None

    try:
        inv = cv2.bitwise_not(edges)
        colored = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
        return cv2.bitwise_and(color_img, colored)
    except Exception:
        return None


def _basic_pipeline(image: np.ndarray, num_colors: int, smoothness: int,
                    edge_method: str, thickness: int, sensitivity: float) -> Optional[np.ndarray]:
    """Common processing used by most styles."""
    _ensure_cv2()
    if image is None:
        return None

    # 1) smooth via bilateral filter
    smooth = apply_bilateral_filter(image, d=smoothness)

    # 2) color quantization
    quant = color_quantization(smooth, k=num_colors)

    # 3) edges
    edges = detect_edges(image, method=edge_method, thickness=thickness, sensitivity=sensitivity)
    return _combine_color_edges(quant, edges)


def apply_classic(image: np.ndarray, num_colors: int = 8, smoothness: int = 5,
                  edge_method: str = "canny", thickness: int = 1,
                  sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Classic cartoon style (baseline)."""
    return _basic_pipeline(image, num_colors, smoothness, edge_method, thickness, sensitivity)


def apply_soft(image: np.ndarray, num_colors: int = 8, smoothness: int = 7,
               edge_method: str = "canny", thickness: int = 1,
               sensitivity: float = 0.8) -> Optional[np.ndarray]:
    """Soft style: blend original image back in for a gentler look."""
    base = apply_classic(image, num_colors, smoothness, edge_method, thickness, sensitivity)
    if base is None:
        return None
    try:
        return cv2.addWeighted(base, 0.6, image, 0.4, 0)
    except Exception:
        return base


def apply_bold(image: np.ndarray, num_colors: int = 4, smoothness: int = 5,
               edge_method: str = "canny", thickness: int = 2,
               sensitivity: float = 1.2) -> Optional[np.ndarray]:
    """Bold style: stronger edges and boosted contrast."""
    cartoon = _basic_pipeline(image, num_colors, smoothness, edge_method, thickness, sensitivity)
    if cartoon is None:
        return None
    try:
        lab = cv2.cvtColor(cartoon, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    except Exception:
        return cartoon


def apply_comic(image: np.ndarray, num_colors: int = 6, smoothness: int = 5,
                edge_method: str = "adaptive", thickness: int = 2,
                sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Comic book style: thicker, hand‑drawn appearance."""
    return _basic_pipeline(image, num_colors, smoothness, edge_method, thickness, sensitivity)


def apply_sketch(image: np.ndarray, num_colors: int = 0, smoothness: int = 0,
                 edge_method: str = "canny", thickness: int = 1,
                 sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Sketch style: return just the line drawing (grayscale)."""
    _ensure_cv2()
    if image is None:
        return None
    edges = detect_edges(image, method=edge_method, thickness=thickness, sensitivity=sensitivity)
    if edges is None:
        return None
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def apply_watercolor(image: np.ndarray, num_colors: int = 4, smoothness: int = 9,
                     edge_method: str = "adaptive", thickness: int = 1,
                     sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Watercolor style: heavy smoothing, pastel palette."""
    # reduce colors more aggressively
    return _basic_pipeline(image, num_colors, smoothness * 2, edge_method, thickness, sensitivity)


def apply_pencil_color(image: np.ndarray, num_colors: int = 0, smoothness: int = 0,
                       edge_method: str = "canny", thickness: int = 1,
                       sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Pencil color style: sketch edges with desaturated color."""
    _ensure_cv2()
    if image is None:
        return None
    if pencil_color_effect is None:
        return None
    return pencil_color_effect(image, blur_ksize=21, saturation_scale=0.5)


def apply_cartoon_style(image: np.ndarray, style: str = "Classic",
                        num_colors: int = 8, smoothness: int = 5,
                        edge_method: str = "canny", thickness: int = 1,
                        sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Dispatch to the selected style function.

    The UI allows users to tweak many parameters, and it is common for
    some combinations (or bad input) to cause the underlying pipeline to
    return ``None``.  Instead of exposing that failure directly to the
    caller we try once with the requested settings and then fall back
    through a small list of safer defaults.  This keeps the Streamlit
    application from showing "Cartoonify failed" for most reasonable
    inputs and gives a better experience by returning *something* even if
    the chosen options were problematic.

    The fallback order is:

    1. Attempt the chosen style and parameters.
    2. If that produces ``None`` try the other built‑in styles using
       a conservative fixed parameter set.
    3. If all styles fail attempt the sketch (line drawing) version.
    4. As a last resort, return a copy of the original image to ensure
       we never return ``None`` unless the input is ``None``.
    """
    styles = {
        "Classic": apply_classic,
        "Soft": apply_soft,
        "Bold": apply_bold,
        "Comic": apply_comic,
        "Sketch": apply_sketch,
        "Watercolor": apply_watercolor,
        "Pencil Color": apply_pencil_color,
    }

    # helper to safely invoke a style and catch exceptions
    def _try_run(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return None

    # 1) try requested combination
    func = styles.get(style, apply_classic)
    result = _try_run(func, image, num_colors, smoothness,
                      edge_method, thickness, sensitivity)
    if result is not None:
        return result

    # 2) cycle through other styles with default safe parameters
    safe_params = {
        "num_colors": 8,
        "smoothness": 5,
        "edge_method": "canny",
        "thickness": 1,
        "sensitivity": 1.0,
    }
    for name, alt in styles.items():
        if name == style:
            continue
        result = _try_run(alt, image, **safe_params)
        if result is not None:
            return result

    # 3) try sketch mode separately (may be more forgiving)
    result = _try_run(apply_sketch, image)
    if result is not None:
        return result

    # 4) give up – return original copy if possible
    if image is not None:
        try:
            return image.copy()
        except Exception:
            pass
    return None


if __name__ == "__main__":
    print("cartoonify module ready")
