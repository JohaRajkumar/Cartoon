import cv2
import numpy as np

# KMeans is only used for color quantization; make it optional so the
# module can be imported even in lean environments.  If it's unavailable
# the quantization step will be skipped.
try:
    from sklearn.cluster import KMeans
except ImportError:  # pragma: no cover - optional dependency
    KMeans = None

# ---------------- BILATERAL FILTER ----------------
def apply_bilateral_filter(img, d=9, sigmaColor=75, sigmaSpace=75):
    """
    Smooth image but keep edges sharp
    """
    return cv2.bilateralFilter(img, d, sigmaColor, sigmaSpace)


# ---------------- COLOR QUANTIZATION ----------------
def color_quantization(img, k=8):
    """
    Reduce number of colors using KMeans.

    If the ``sklearn`` package couldn't be imported we simply return a
    copy of the original image (no quantization).  This keeps the
    rest of the pipeline working in minimal installations and mirrors the
    way the Streamlit UI tells users to "try different settings" when
    cartoonify fails: if quantization can't run we don't crash, we just
    skip it.
    """
    if img is None:
        return None
    if KMeans is None or k <= 0:
        # nothing to do
        return img.copy()

    data = img.reshape((-1, 3))
    data = np.float32(data)

    try:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(data)
        centers = np.uint8(kmeans.cluster_centers_)
        quantized = centers[labels.flatten()]
        quantized = quantized.reshape(img.shape)
        return quantized
    except Exception:
        # if clustering fails, just return original
        try:
            return img.copy()
        except Exception:
            return img


# ---------------- CARTOON EFFECT ----------------
def cartoonify_image(image_path, num_colors=8, blur_strength=7):
    """
    Full cartoon pipeline
    """

    # read image
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not found or path incorrect")

    # resize (optional for speed)
    img = cv2.resize(img, (600, 600))

    # bilateral filter (smooth)
    smooth = apply_bilateral_filter(img, d=blur_strength)

    # color reduction
    quantized = color_quantization(smooth, k=num_colors)

    # edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)

    edges = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        9,
        9
    )

    edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    # combine color + edges
    cartoon = cv2.bitwise_and(quantized, edges)

    return cartoon