import os
import sys

# ensure top‑level project folder is on import path when running tests
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pytest

try:
    import cv2
except ImportError:  # type: ignore
    cv2 = None

try:
    import sklearn  # just check availability
except ImportError:  # type: ignore
    sklearn = None

from cartoonify import apply_cartoon_style


def make_dummy():
    # simple grayscale gradient with optional rectangle
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    if cv2 is not None:
        cv2.rectangle(img, (5, 5), (45, 45), (255, 255, 255), -1)
    return img


def test_uniform_input_returns_array():
    """A very simple image (all zeros) should still produce an array.

    The output may be identical to the input, but it shouldn't be ``None``.
    """
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    out = apply_cartoon_style(img)
    assert out is not None
    assert isinstance(out, np.ndarray)


@pytest.mark.skipif(cv2 is None or sklearn is None,
                       reason="OpenCV and scikit-learn required")
def test_cartoon_styles():
    img = make_dummy()
    styles = ["Classic", "Soft", "Bold", "Comic", "Sketch", "Watercolor"]
    for style in styles:
        output = apply_cartoon_style(img, style=style, num_colors=5, smoothness=3,
                                     edge_method="canny", thickness=1, sensitivity=1.0)
        assert output is not None
        assert isinstance(output, np.ndarray)
        # check same height/width
        assert output.shape[0] == img.shape[0]
        assert output.shape[1] == img.shape[1]


def test_cartoon_edge_methods():
    """Ensure cartoonify works with every supported edge detection mode."""
    if cv2 is None or sklearn is None:
        pytest.skip("OpenCV/scikit-learn not available, cannot run edge method test")

    img = make_dummy()
    methods = ["canny", "adaptive", "gray", "sobel", "laplacian"]
    for m in methods:
        out = apply_cartoon_style(img, style="Classic", num_colors=5,
                                  smoothness=3, edge_method=m,
                                  thickness=1, sensitivity=1.0)
        assert out is not None
        assert isinstance(out, np.ndarray)
        assert out.shape == img.shape


def test_cartoonify_fallback(monkeypatch):
    """If the chosen style fails, the function should still return an array.

    We simulate failure by having the first style raise/return None and
    verify that a fallback result is produced instead of propagating
    ``None``.
    """
    if cv2 is None or sklearn is None:
        pytest.skip("OpenCV/scikit-learn not available, cannot run fallback test")

    img = make_dummy()

    # force the requested style to fail first
    monkeypatch.setattr('cartoonify.apply_classic', lambda *args, **kwargs: None)

    output = apply_cartoon_style(img, style="Classic", num_colors=5,
                                 smoothness=3, edge_method="canny",
                                 thickness=1, sensitivity=1.0)
    assert output is not None
    assert isinstance(output, np.ndarray)
    # output may be original image when all else fails
    assert output.shape == img.shape

    # now simulate *all* style functions failing so we hit the final fallback
    for funcname in [
        'apply_classic', 'apply_soft', 'apply_bold',
        'apply_comic', 'apply_sketch', 'apply_watercolor'
    ]:
        monkeypatch.setattr(f'cartoonify.{funcname}', lambda *args, **kwargs: None)

    output2 = apply_cartoon_style(img)
    assert output2 is not None
    assert isinstance(output2, np.ndarray)
    # because every style returned None the implementation returns a copy
    # at a minimum we expect the dimensions to match the input
    assert output2.shape == img.shape
