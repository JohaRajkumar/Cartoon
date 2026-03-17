import cv2
import numpy as np
from sklearn.cluster import KMeans


# ------------------ RESIZE FOR PERFORMANCE ------------------
def resize_image(img, max_width=800):
    h, w = img.shape[:2]
    if w > max_width:
        ratio = max_width / w
        new_dim = (int(w * ratio), int(h * ratio))
        img = cv2.resize(img, new_dim, interpolation=cv2.INTER_AREA)
    return img


# ------------------ COLOR QUANTIZATION ------------------
def color_quantization(img, k=8):
    data = np.float32(img).reshape((-1, 3))

    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(data)
    centers = np.uint8(kmeans.cluster_centers_)

    quantized = centers[labels.flatten()]
    quantized = quantized.reshape(img.shape)

    return quantized


# ------------------ EDGE DETECTION ------------------
def detect_edges(img_gray, method="canny"):
    if method == "canny":
        edges = cv2.Canny(img_gray, 100, 200)
    else:
        edges = cv2.adaptiveThreshold(
            img_gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            9, 9
        )
    return edges


# ------------------ MAIN CARTOON FUNCTION ------------------
def apply_classic_cartoon(image_or_path, intensity="medium", num_colors=None, smoothness=None):

    # accept either a numpy image array or a path
    if isinstance(image_or_path, np.ndarray):
        img = image_or_path
    else:
        img = cv2.imread(image_or_path)
        if img is None:
            raise ValueError("Invalid image path")

    # resize for performance
    img = resize_image(img)

    # convert to gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # smooth noise
    gray = cv2.medianBlur(gray, 5)

    # intensity default settings
    if intensity == "light":
        k = 12
        blur = 7
    elif intensity == "strong":
        k = 6
        blur = 15
    else:  # medium
        k = 8
        blur = 10

    # allow explicit overrides
    if num_colors is not None:
        try:
            k = int(num_colors)
        except Exception:
            pass

    if smoothness is not None:
        try:
            blur = int(smoothness)
        except Exception:
            pass

    # bilateral filter (paint effect)
    smooth = cv2.bilateralFilter(img, d=9, sigmaColor=blur * 10, sigmaSpace=blur)

    # color reduction
    quantized = color_quantization(smooth, k=k)

    # edges
    edges = detect_edges(gray, method="canny")

    # invert edges
    edges = cv2.bitwise_not(edges)

    # convert to color
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    # combine color + edges
    cartoon = cv2.bitwise_and(quantized, edges_colored)

    return cartoon