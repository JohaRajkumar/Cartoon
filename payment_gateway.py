import os
import sqlite3
import logging
from datetime import datetime, timezone

# load environment variables from .env if python-dotenv is installed
DOTENV_LOADED = False
try:
    from dotenv import load_dotenv
    DOTENV_LOADED = load_dotenv()
except ImportError:
    # not required but convenient during development
    DOTENV_LOADED = False

# razorpay is optional at import time; we'll raise meaningful errors if
# someone tries to use payment functionality without installing it.
try:
    import razorpay
    HAS_RAZORPAY = True
except ImportError:
    razorpay = None  # type: ignore
    HAS_RAZORPAY = False
    logging.getLogger(__name__).warning(
        "razorpay package not found; payment functions will be disabled"
    )


def get_razorpay_keys():
    """Return (key_id, key_secret) from environment. """
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    return key_id, key_secret


def is_razorpay_configured():
    """Return True if Razorpay keys are present and not placeholders."""
    key_id, key_secret = get_razorpay_keys()
    if not key_id or not key_secret:
        return False
    if "your_test" in key_id or "your_test" in key_secret:
        return False
    if "your_key_here" in key_id or "your_key_here" in key_secret:
        return False
    return True

# configure logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# database constant (reuse same file as other modules)
from database import DB_NAME

# ------------------------------------
# Razorpay client initialization
# ------------------------------------

def _get_razorpay_client():
    """Return a configured Razorpay client using environment variables.

    Raises
    ------
    RuntimeError
        If razorpay is not installed or keys are missing or clearly invalid.
    razorpay.errors.AuthenticationError
        If the provided credentials are invalid at API level.
    """
    if not HAS_RAZORPAY:
        raise RuntimeError("razorpay library is not installed")

    key_id, key_secret = get_razorpay_keys()

    if not key_id or not key_secret:
        msg = "Razorpay API key/secret not configured in environment"
        logger.error(msg)
        raise RuntimeError(msg)

    # rudimentary check for placeholder values
    placeholder_detected = False
    for val in (key_id, key_secret):
        if "your_test" in val or val.strip() == "" or "your_key_here" in val:
            logger.warning(
                "Razorpay environment variable appears to be a placeholder: %s; "
                "payments will run in dummy mode until real keys are configured",
                val,
            )
            placeholder_detected = True

    if placeholder_detected:
        # return a simple dummy client so the rest of the application can
        # exercise order/verification logic without raising errors.
        class _DevDummyClient:
            class order:
                @staticmethod
                def create(data):
                    return {"id": "order_DEV", "amount": data.get("amount")}

            class utility:
                @staticmethod
                def verify_payment_signature(data):
                    if data.get("razorpay_signature") != "good":
                        raise Exception("SignatureVerificationError")

        return _DevDummyClient()

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        return client
    except Exception as exc:
        auth_err = getattr(razorpay.errors, "AuthenticationError", None)
        if auth_err and isinstance(exc, auth_err):
            logger.error("Authentication failed when creating razorpay client: %s", exc)
            raise

        # Some razorpay versions may not expose AuthenticationError class.
        # We still want the error to be visible for debugging, then re-raise.
        logger.error("Failed to initialize Razorpay client: %s", exc)
        raise


# ------------------------------------
# Payment utility functions
# ------------------------------------

def create_payment_order(amount, currency="INR", receipt_id=None):
    if not HAS_RAZORPAY:
        raise RuntimeError("create_payment_order called but razorpay is unavailable")
    """Create a new Razorpay order.

    Parameters
    ----------
    amount : int or float
        Amount in rupees; will be converted to paise (multiply by 100).
    currency : str
        Currency code (default ``INR``).
    receipt_id : str or None
        Optional identifier for your own bookkeeping.

    Returns
    -------
    tuple
        ``(order_id, order_dict)`` on success.

    Raises
    ------
    razorpay.errors.RazorpayError
        When the Razorpay API returns an error.
    """
    client = _get_razorpay_client()

    # convert to paise (integer)
    try:
        paise = int(round(float(amount) * 100))
    except Exception as exc:
        logger.exception("Invalid amount passed to create_payment_order")
        raise

    payload = {
        "amount": paise,
        "currency": currency,
        # use timezone-aware UTC timestamp when generating a receipt id
        "receipt": receipt_id or f"rcpt_{datetime.now(timezone.utc).timestamp()}",
        "payment_capture": 1,  # auto capture
    }
    try:
        order = client.order.create(data=payload)
        order_id = order.get("id")
        logger.info("Created razorpay order %s for %s paise", order_id, paise)
        print("Payment order created successfully", order_id)
        return order_id, order
    except razorpay.errors.AuthenticationError:
        logger.error("Razorpay authentication failed - check your API key/secret")
        raise
    except Exception as exc:  # catch RazorpayError, network issues, etc.
        logger.exception("Failed to create Razorpay order")
        raise


def verify_payment_signature(order_id, payment_id, signature):
    if not HAS_RAZORPAY:
        logger.warning("verify_payment_signature called without razorpay")
        return False
    """Verify signature of a Razorpay payment.

    Parameters are taken from Razorpay's post-payment webhook/callback.
    Returns ``True`` when the signature matches, ``False`` otherwise.
    """
    client = _get_razorpay_client()
    data = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }
    try:
        client.utility.verify_payment_signature(data)
        logger.info("Payment verified for order %s", order_id)
        print("Payment verified")
        return True
    except razorpay.errors.SignatureVerificationError:
        logger.warning("Invalid signature for payment %s", payment_id)
        return False
    except Exception:
        logger.exception("Unexpected error verifying payment signature")
        return False


def update_transaction_status(order_id, payment_id, status, amount, user_id=None):
    """Insert or update a transaction record in the database.

    ``amount`` should be provided in paise (integer) to remain consistent
    with Razorpay's API. ``status`` is a short string such as ``pending``,
    ``success`` or ``failed``.

    The function will ensure the transactions table exists by invoking
    ``database.create_tables()`` if needed.
    """
    # make sure DB schema is ready
    try:
        from database import create_tables
        create_tables()
    except Exception:
        # if import fails just continue; table creation might be manual
        logger.debug("Could not import create_tables; assuming schema exists")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # use timezone-aware UTC timestamp to avoid deprecation warning
    timestamp = datetime.now(timezone.utc).isoformat()

    # look for existing row
    cursor.execute(
        "SELECT id FROM transactions WHERE order_id = ?", (order_id,)
    )
    row = cursor.fetchone()
    try:
        if row:
            cursor.execute(
                """
                UPDATE transactions
                SET payment_id = ?, amount = ?, status = ?, timestamp = ?
                WHERE order_id = ?
                """,
                (payment_id, amount, status, timestamp, order_id),
            )
            logger.info("Updated transaction %s -> %s", order_id, status)
        else:
            cursor.execute(
                """
                INSERT INTO transactions
                    (user_id, order_id, payment_id, amount, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, order_id, payment_id, amount, status, timestamp),
            )
            logger.info("Inserted new transaction %s", order_id)
            print("Transaction saved to database", order_id)
        conn.commit()
    except Exception:
        logger.exception("Database error while updating transaction")
        conn.rollback()
        raise
    finally:
        conn.close()


def handle_webhook(request_data: dict):
    """Process a Razorpay webhook payload.

    Parameters
    ----------
    request_data : dict
        The JSON payload sent by Razorpay. It must already have been parsed from
        the HTTP body. Signature verification (using headers) should be done by
        the caller before invoking this helper.

    Behavior
    --------
    - On ``payment.captured`` updates the corresponding transaction to ``success``.
    - On ``payment.failed`` updates the transaction to ``failed``.
    - Other events are logged and ignored.
    """
    event = request_data.get("event")
    payload = request_data.get("payload", {})

    if event == "payment.captured":
        payment = payload.get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        amount = payment.get("amount")  # already in paise
        update_transaction_status(order_id, payment_id, "success", amount)
    elif event == "payment.failed":
        payment = payload.get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        amount = payment.get("amount")
        update_transaction_status(order_id, payment_id, "failed", amount)
    else:
        logger.info("Unhandled webhook event: %s", event)


def verify_transaction(user_id, order_id):
    """Return True only if the transaction exists and is successful for the user."""
    from database import create_tables

    create_tables()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT status FROM transactions
        WHERE order_id = ? AND user_id = ?
        """,
        (order_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    return bool(row and row[0] == "success")


def get_transaction(user_id, order_id):
    """Return transaction row dict for given user and order_id."""
    from database import create_tables

    create_tables()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM transactions
        WHERE order_id = ? AND user_id = ?
        """,
        (order_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_transaction_history(user_id, limit=100):
    """Return list of recent transactions for user."""
    from database import create_tables

    create_tables()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------
# Example usage (not executed on import)
#
# To test this module manually, create a .env file in the project root
# containing your Razorpay test credentials:
#
#   RAZORPAY_KEY_ID=rzp_test_xxx
#   RAZORPAY_KEY_SECRET=yyy
#
# Then run:
#   python payment_gateway.py
#
# This will create a dummy order and print verification outcomes.
# --------------------------------------------------
if __name__ == "__main__":
    if not HAS_RAZORPAY:
        print("razorpay not installed; cannot run example usage")
    else:
        # Ensure env variables are set in your shell before running:
        # export RAZORPAY_KEY_ID="rzp_test_xxx"
        # export RAZORPAY_KEY_SECRET="yyy"

        # create an order for ₹10
        try:
            oid, details = create_payment_order(10, receipt_id="test123")
            print("order created", oid)
        except Exception as e:
            print("failed to create order", e)

        # simulate verifying a payment (values would come from frontend)
        fake_order = "order_ABC"
        fake_payment = "pay_123"
        fake_sig = "invalid"
        print("signature valid?", verify_payment_signature(fake_order, fake_payment, fake_sig))

        # for testing with Razorpay test cards see:
        # https://razorpay.com/docs/payment-gateway/testing/test-card-upi-details/
