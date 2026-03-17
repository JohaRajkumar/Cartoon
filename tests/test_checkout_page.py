import os
import sys
import numpy as np
import cv2
from PIL import Image
import streamlit as st

# make sure pages package is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pages import checkout


def test_limit_pil_image():
    # create a wide image and ensure it's resized
    pil = Image.new("RGB", (1200, 300), color=(255, 0, 0))
    result = checkout._limit_pil_image(pil, maxw=600, maxh=600)
    assert result.size[0] <= 600 and result.size[1] <= 600


def test_payment_helpers_exist():
    # page should import the Razorpay helpers even if razorpay missing
    assert hasattr(checkout, "create_payment_order")
    assert hasattr(checkout, "verify_payment_signature")
    assert hasattr(checkout, "update_transaction_status")
    assert hasattr(checkout, "prepare_image_for_download")


def test_show_checkout_callable(monkeypatch):
    # calling the display function should not crash even when session lacks keys
    monkeypatch.setitem(st.session_state, "user", "testuser")
    # ensure required keys exist to avoid early stop
    monkeypatch.setitem(st.session_state, "cartoon_result", np.zeros((2,2,3), dtype=np.uint8))
    monkeypatch.setitem(st.session_state, "adjusted_image", np.zeros((2,2,3), dtype=np.uint8))
    # call the function; errors will surface if broken
    checkout.show_checkout_page()


def test_login_required(monkeypatch):
    # when no user is logged in we shouldn't crash (link shown)
    monkeypatch.setitem(st.session_state, "user", None)
    # ensure cartoon_result absence triggers earlier stop
    monkeypatch.setitem(st.session_state, "cartoon_result", None)
    try:
        checkout.show_checkout_page()
    except Exception as e:
        pytest.fail(f"login branch failed: {e}")


def test_page_importable():
    # simply importing the module should not raise errors
    # pylint: disable=unused-variable
    mod = checkout
    assert mod is not None
