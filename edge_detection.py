"""edge_detection.py
Utilities for detecting and processing edges to produce cartoon-style outlines.

Functions:
- apply_canny_edge
- apply_adaptive_threshold
- apply_median_blur
- adjust_edge_thickness
- detect_edges
- compare_images

The module is written to work with images loaded via `cv2.imread` (NumPy arrays).
If OpenCV (`cv2`) is not installed, functions will raise a helpful RuntimeError.
"""

from typing import Optional

try:
    import cv2
except Exception:  # pragma: no cover - runtime dependency
    cv2 = None

import numpy as np


def _ensure_cv2():
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) is required. Install it with `pip install opencv-python`")


def apply_median_blur(image: np.ndarray, kernel_size: int = 5) -> Optional[np.ndarray]:
    """Apply median blur to reduce noise.

    Parameters
    - image: Input BGR or grayscale image as NumPy array.
    - kernel_size: Odd integer kernel size (will be adjusted to next odd if even).

    Returns blurred image or None for invalid input.
    """
    _ensure_cv2()
    if image is None:
        return None
    k = int(kernel_size)
    if k % 2 == 0:
        k += 1
    if k < 1:
        k = 1
    try:
        return cv2.medianBlur(image, k)
    except Exception:
        return None


def apply_canny_edge(image: np.ndarray, low_threshold: int = 100, high_threshold: int = 200) -> Optional[np.ndarray]:
    """Convert image to grayscale, blur, and apply Canny edge detection.

    Parameters
    - image: Input BGR image as NumPy array.
    - low_threshold: Lower threshold for hysteresis.
    - high_threshold: Upper threshold for hysteresis.

    Returns binary edge image (uint8) or None if input invalid.
    """
    _ensure_cv2()
    if image is None:
        return None

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, max(1, int(low_threshold)), max(1, int(high_threshold)))
        return edges
    except Exception:
        return None


def apply_adaptive_threshold(image: np.ndarray, block_size: int = 9, C: int = 2) -> Optional[np.ndarray]:
    """Create edge-like image using adaptive thresholding.

    Steps:
    - Convert to grayscale
    - Median blur to reduce noise
    - Apply adaptive threshold (mean)

    Returns binary edge image or None on error.
    """
    _ensure_cv2()
    if image is None:
        return None

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        bsize = int(block_size)
        if bsize % 2 == 0:
            bsize += 1
        if bsize < 3:
            bsize = 3

        blurred = cv2.medianBlur(gray, 5)
        thresh = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            bsize,
            C,
        )
        return thresh
    except Exception:
        return None


def adjust_edge_thickness(edge_image: np.ndarray, thickness: int = 1) -> Optional[np.ndarray]:
    """Increase the thickness of edges using dilation.

    Parameters
    - edge_image: Binary edge image (uint8)
    - thickness: Positive integer controlling dilation amount

    Returns thickened edge image or None on error.
    """
    _ensure_cv2()
    if edge_image is None:
        return None
    try:
        t = max(1, int(thickness))
        # kernel sized based on thickness: make it odd and scale
        k = t * 2 + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        dilated = cv2.dilate(edge_image, kernel, iterations=1)
        return dilated
    except Exception:
        return None


def detect_edges(image: np.ndarray, method: str = "canny", thickness: int = 1, sensitivity: float = 1.0) -> Optional[np.ndarray]:
    """Detect edges using specified method and adjust thickness.

    Supported methods:
    - "canny": standard Canny edge detector with threshold scaling
    - "adaptive": adaptive threshold sketch-style edges
    - "gray": simply convert to grayscale (useful as a neutral baseline)
    - "sobel": Sobel gradient magnitude
    - "laplacian": Laplacian second-derivative edges

    Parameters
    - image: Input BGR image as NumPy array (as read by cv2.imread)
    - method: one of the supported strings above
    - thickness: edge thickness multiplier
    - sensitivity: scales threshold values (only affects "canny" and "adaptive")

    Returns final edge image (uint8) or None if error.
    """
    _ensure_cv2()
    if image is None:
        return None

    m = method.lower()
    try:
        if m == "canny":
            # Base thresholds; sensitivity scales them
            base_low, base_high = 100, 200
            scale = float(sensitivity) if sensitivity > 0 else 1.0
            low = max(1, int(base_low * scale))
            high = max(low + 1, int(base_high * scale))
            edges = apply_canny_edge(image, low_threshold=low, high_threshold=high)

        elif m == "adaptive":
            # scale block size by sensitivity (ensure odd)
            base_block = 9
            b = int(max(3, base_block * (sensitivity if sensitivity > 0 else 1)))
            if b % 2 == 0:
                b += 1
            edges = apply_adaptive_threshold(image, block_size=b, C=2)

        elif m == "gray":
            # simply return a grayscale version of the image; thickness will still dilate
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
            edges = gray

        elif m == "sobel":
            # magnitude of Sobel gradients (approximate edges)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
            # normalize to 0-255
            if mag.max() != 0:
                mag = (mag / mag.max() * 255).astype(np.uint8)
            else:
                mag = mag.astype(np.uint8)
            edges = mag

        elif m == "laplacian":
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
            lap = cv2.Laplacian(gray, cv2.CV_64F)
            lap = np.absolute(lap)
            if lap.max() != 0:
                lap = (lap / lap.max() * 255).astype(np.uint8)
            else:
                lap = lap.astype(np.uint8)
            edges = lap

        else:
            raise ValueError(f"Unknown method '{method}'. Choose 'canny', 'adaptive', 'gray', 'sobel' or 'laplacian'.")

        if edges is None:
            return None

        thick = adjust_edge_thickness(edges, thickness=thickness)
        return thick
    except Exception:
        return None


def compare_images(original: np.ndarray, edges: np.ndarray) -> Optional[np.ndarray]:
    """Resize both images to the same height and stack them side-by-side.

    Returns the combined image (BGR) or None on error.
    """
    _ensure_cv2()
    if original is None or edges is None:
        return None
    try:
        # convert single-channel edges to BGR for stacking
        if len(edges.shape) == 2:
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        else:
            edges_bgr = edges.copy()

        h = original.shape[0]
        w = original.shape[1]

        edges_resized = cv2.resize(edges_bgr, (w, h), interpolation=cv2.INTER_AREA)
        combined = np.hstack([original, edges_resized])
        return combined
    except Exception:
        return None


if __name__ == "__main__":
    # simple smoke test when run directly (will not execute if cv2 missing)
    try:
        _ensure_cv2()
        print("edge_detection module loaded. Call functions from your app.")
    except RuntimeError as e:
        print(e)
