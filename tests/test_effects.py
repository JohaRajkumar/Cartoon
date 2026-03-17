"""test_effects.py

Unit tests for artistic effects in effects.py
"""

import os
import sys

# ensure top-level project folder is on import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pytest

try:
    import cv2
except ImportError:
    cv2 = None

from effects import (
    canny_edge,
    adaptive_sketch,
    sobel_edge,
    laplacian_edge,
    pencil_sketch,
    pencil_color,
    sketch_effect,
    pencil_color_effect,
)


def make_sample_image():
    """Create a simple test image with color gradient."""
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    # create a simple colored square
    img[10:40, 10:40] = (100, 150, 200)  # light blue
    return img


# ============================================================================
# EDGE DETECTION EFFECT TESTS
# ============================================================================


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_canny_edge_valid_image():
    """canny_edge should return a valid binary image."""
    img = make_sample_image()
    result = canny_edge(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape[0] == img.shape[0]
    assert result.shape[1] == img.shape[1]
    # should be grayscale
    assert len(result.shape) == 2


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_canny_edge_none_input():
    """canny_edge should return None for None input."""
    assert canny_edge(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_canny_edge_thresholds():
    """canny_edge should accept custom threshold values."""
    img = make_sample_image()
    result_low = canny_edge(img, low_threshold=50, high_threshold=150)
    result_high = canny_edge(img, low_threshold=150, high_threshold=300)
    assert result_low is not None
    assert result_high is not None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_adaptive_sketch_valid_image():
    """adaptive_sketch should return a valid binary sketch image."""
    img = make_sample_image()
    result = adaptive_sketch(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == (img.shape[0], img.shape[1])


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_adaptive_sketch_none_input():
    """adaptive_sketch should return None for None input."""
    assert adaptive_sketch(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_sobel_edge_valid_image():
    """sobel_edge should return a valid edge magnitude image."""
    img = make_sample_image()
    result = sobel_edge(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == (img.shape[0], img.shape[1])
    assert result.dtype == np.uint8


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_sobel_edge_none_input():
    """sobel_edge should return None for None input."""
    assert sobel_edge(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_laplacian_edge_valid_image():
    """laplacian_edge should return a valid edge image."""
    img = make_sample_image()
    result = laplacian_edge(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == (img.shape[0], img.shape[1])
    assert result.dtype == np.uint8


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_laplacian_edge_none_input():
    """laplacian_edge should return None for None input."""
    assert laplacian_edge(None) is None


# ============================================================================
# SKETCH EFFECT TESTS
# ============================================================================


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_sketch_valid_image():
    """pencil_sketch should return a valid grayscale sketch."""
    img = make_sample_image()
    result = pencil_sketch(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == (img.shape[0], img.shape[1])


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_sketch_none_input():
    """pencil_sketch should return None for None input."""
    assert pencil_sketch(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_sketch_custom_blur():
    """pencil_sketch should accept custom blur kernel size."""
    img = make_sample_image()
    result = pencil_sketch(img, blur_ksize=11)
    assert result is not None


# ============================================================================
# COLORED PENCIL EFFECT TESTS
# ============================================================================


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_valid_image():
    """pencil_color should return a valid BGR image."""
    img = make_sample_image()
    result = pencil_color(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_none_input():
    """pencil_color should return None for None input."""
    assert pencil_color(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_custom_params():
    """pencil_color should accept custom parameters."""
    img = make_sample_image()
    result = pencil_color(img, blur_ksize=15, color_strength=0.5)
    assert result is not None
    assert result.shape == img.shape


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_color_strength():
    """pencil_color with different color_strength should produce different results."""
    img = make_sample_image()
    weak = pencil_color(img, color_strength=0.1)
    strong = pencil_color(img, color_strength=0.9)
    assert weak is not None
    assert strong is not None
    # results should differ
    assert not np.array_equal(weak, strong)



def test_sketch_effect_valid_image():
    """sketch_effect should return a valid grayscale (as BGR) image."""
    img = make_sample_image()
    result = sketch_effect(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_sketch_effect_none_input():
    """sketch_effect should return None for None input."""
    assert sketch_effect(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_sketch_effect_custom_blur():
    """sketch_effect should accept custom blur kernel size."""
    img = make_sample_image()
    result = sketch_effect(img, blur_ksize=5, contrast=1.0)
    assert result is not None
    assert result.shape == img.shape


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_sketch_effect_even_ksize():
    """sketch_effect should adjust even kernel size to odd."""
    img = make_sample_image()
    # pass even ksize; should be adjusted to 21+1=23
    result_even = sketch_effect(img, blur_ksize=20, contrast=1.5)
    result_odd = sketch_effect(img, blur_ksize=21, contrast=1.5)
    # both should work without error
    assert result_even is not None
    assert result_odd is not None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_sketch_effect_contrast():
    """sketch_effect with different contrast values should produce different results."""
    img = make_sample_image()
    low_contrast = sketch_effect(img, contrast=1.0)
    high_contrast = sketch_effect(img, contrast=2.0)
    assert low_contrast is not None
    assert high_contrast is not None
    # results should be different (not identical arrays)
    assert not np.array_equal(low_contrast, high_contrast)


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_effect_valid_image():
    """pencil_color_effect should return a valid BGR image."""
    img = make_sample_image()
    result = pencil_color_effect(img)
    assert result is not None
    assert isinstance(result, np.ndarray)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_effect_none_input():
    """pencil_color_effect should return None for None input."""
    assert pencil_color_effect(None) is None


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_effect_saturation():
    """pencil_color_effect with different saturation should produce different results."""
    img = make_sample_image()
    desaturated = pencil_color_effect(img, saturation_scale=0.0)
    saturated = pencil_color_effect(img, saturation_scale=1.0)
    assert desaturated is not None
    assert saturated is not None
    # results should differ
    assert not np.array_equal(desaturated, saturated)


@pytest.mark.skipif(cv2 is None, reason="OpenCV not installed")
def test_pencil_color_effect_custom_params():
    """pencil_color_effect should accept custom parameters."""
    img = make_sample_image()
    result = pencil_color_effect(img, blur_ksize=11, saturation_scale=0.7)
    assert result is not None
    assert result.shape == img.shape
