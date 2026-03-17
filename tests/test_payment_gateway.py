import os
import sqlite3
from datetime import datetime

# ensure project path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest

# if razorpay isn't installed, skip the whole module
from payment_gateway import HAS_RAZORPAY
if not HAS_RAZORPAY:
    pytest.skip("razorpay package missing; skipping payment gateway tests", allow_module_level=True)

from payment_gateway import (
    create_payment_order,
    verify_payment_signature,
    update_transaction_status,
    handle_webhook,
    DB_NAME,
)


class DummyClient:
    def __init__(self, auth=None):
        pass

    class order:
        @staticmethod
        def create(data):
            # echo back something minimal
            return {"id": "order_TEST", "amount": data.get("amount")}

    class utility:
        @staticmethod
        def verify_payment_signature(data):
            # simple rule: if signature == "good" it passes
            if data.get("razorpay_signature") != "good":
                raise Exception("SignatureVerificationError")


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    # monkeypatch the internal _get_razorpay_client to return dummy
    import payment_gateway

    monkeypatch.setattr(payment_gateway, "_get_razorpay_client", lambda: DummyClient())
    yield
    # clean db file after each test
    try:
        os.remove(DB_NAME)
    except Exception:
        pass


def test_create_payment_order_converts_amount():
    oid, details = create_payment_order(10, receipt_id="r1")
    assert oid == "order_TEST"
    assert details["amount"] == 1000


def test_verify_payment_signature():
    assert verify_payment_signature("o", "p", "good") is True
    assert verify_payment_signature("o", "p", "bad") is False


def test_placeholder_keys_use_dummy_client(monkeypatch):
    # set obvious-placeholder values in the environment and verify the
    # module falls back to the dummy client created by _get_razorpay_client.
    # The autouse fixture normally replaces the client with a test dummy so
    # we reload the module here to undo that patch.
    import importlib
    import payment_gateway

    monkeypatch.setenv("RAZORPAY_KEY_ID", "your_test_key")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "your_test_secret")

    payment_gateway = importlib.reload(payment_gateway)

    oid, details = payment_gateway.create_payment_order(5)  # ₹5 => 500 paise
    assert oid == "order_DEV"  # dummy client order id from placeholder fallback
    assert details["amount"] == 500

    # signature checks still operate against dummy rules
    assert payment_gateway.verify_payment_signature("o", "p", "good") is True
    assert payment_gateway.verify_payment_signature("o", "p", "bad") is False


def test_update_transaction_status_insert_and_update():
    # ensure fresh db; make table
    from database import create_tables

    create_tables()
    update_transaction_status("ord1", "pay1", "pending", 500, user_id=7)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT order_id, payment_id, amount, status FROM transactions WHERE order_id=?", ("ord1",))
    row = cur.fetchone()
    assert row == ("ord1", "pay1", 500, "pending")

    # update status
    update_transaction_status("ord1", "pay1", "success", 500)
    cur.execute("SELECT status FROM transactions WHERE order_id=?", ("ord1",))
    assert cur.fetchone()[0] == "success"
    conn.close()


def test_handle_webhook_captured_and_failed():
    from database import create_tables

    create_tables()
    payload = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"order_id": "o1", "id": "p1", "amount": 123}}},
    }
    handle_webhook(payload)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT status FROM transactions WHERE order_id=?", ("o1",))
    assert cur.fetchone()[0] == "success"

    payload2 = {
        "event": "payment.failed",
        "payload": {"payment": {"entity": {"order_id": "o1", "id": "p1", "amount": 123}}},
    }
    handle_webhook(payload2)
    cur.execute("SELECT status FROM transactions WHERE order_id=?", ("o1",))
    assert cur.fetchone()[0] == "failed"
    conn.close()
