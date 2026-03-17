import numpy as np
import cv2
from edge_detection import (
    apply_canny_edge,
    apply_adaptive_threshold,
    apply_median_blur,
    adjust_edge_thickness,
    detect_edges,
)


def make_test_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (10, 10), (90, 90), (255, 255, 255), -1)
    return img


def test_canny():
    img = make_test_image()
    edges = apply_canny_edge(img)
    assert edges is not None
    assert edges.dtype == np.uint8


def test_adaptive():
    img = make_test_image()
    thresh = apply_adaptive_threshold(img)
    assert thresh is not None
    assert thresh.dtype == np.uint8


def test_blur_and_thicken():
    img = make_test_image()
    blurred = apply_median_blur(img, 5)
    assert blurred is not None
    edges = apply_canny_edge(blurred)
    thick = adjust_edge_thickness(edges, 2)
    assert thick is not None


def test_detect_edges_variants():
    """detect_edges should handle every supported method name."""
    img = make_test_image()
    methods = ["canny", "adaptive", "gray", "sobel", "laplacian"]
    for m in methods:
        edges = detect_edges(img, method=m, thickness=1, sensitivity=1.0)
        assert edges is not None
        assert edges.dtype == np.uint8

    # unknown method should be treated gracefully (return None)
    assert detect_edges(img, method="unknown", thickness=1, sensitivity=1.0) is None
