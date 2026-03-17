# Cartoon Project

This application provides image cartoonification and includes features
such as user account handling, image downloads, and a payment gateway
integration using Razorpay.

## Environment Setup

Copy `.env.example` (if provided) or edit the `.env` file directly to set
sensitive configuration values. At minimum, you should specify:

```
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXX
```

> **Important:**
> 
> - These must be *real* test credentials obtained from your Razorpay
>   dashboard (https://dashboard.razorpay.com).
> - Using placeholder values like `rzp_test_your_key_here` or leaving the
  variables blank will trigger a log **warning**. In development the
  module will automatically fall back to a built‑in dummy client so the
  app continues working without crashing; however this dummy mode does not
  communicate with Razorpay and should not be used for real transactions.
- Replace placeholders with actual keys before running a production
  deployment or doing any real payment testing.

## Running the Server (new one-command launcher)

You can launch the Streamlit app with a single command (recommended):

```bash
python run_server.py
```

By default this runs on `http://0.0.0.0:8501`, but you can change host/port in terminal:

```bash
python run_server.py --port 8501 --address 127.0.0.1
```

To keep it headless (no browser pop-up):

```bash
python run_server.py --nogui
```

This wrapper uses your active Python environment and configures options consistently.

## Running Tests

All modules include unit tests under `tests/`. They are designed to run
without actual Razorpay credentials by monkeypatching the client. To
execute the suite:

```bash
pip install -r requirements.txt
pytest -q
```

## Notes

- The download module records metadata in a local SQLite database
  (`app.db`).
- Old download files are pruned automatically by `delete_old_files`.
- Payment gateway logic is largely wrapped in `payment_gateway.py` and
  can be invoked directly for simple testing.
