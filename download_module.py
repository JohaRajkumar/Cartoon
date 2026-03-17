import os
import sqlite3
from datetime import datetime, timedelta

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# database name (reuse same DB as other modules)
from database import DB_NAME

# ---------------------------------------------------------------------------
# Helper/database functions
# ---------------------------------------------------------------------------

def _ensure_download_table_exists():
    """Ensure the ImageHistory table exists."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ImageHistory (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_id INTEGER,
            style TEXT,
            download_timestamp TEXT,
            filename TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_download_metadata(user_id: int, image_id: int, style: str, filename: str):
    """Insert a record into the ImageHistory table when a user downloads an image.

    Parameters:
        user_id: the id of the user performing the download
        image_id: the id of the processed image (if available)
        style: string description of the style applied
        filename: the actual filename that was generated for download (not full path)
    """
    try:
        _ensure_download_table_exists()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ImageHistory (user_id, image_id, style, download_timestamp, filename)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, image_id, style, datetime.now().isoformat(), filename),
        )
        conn.commit()
    except Exception as e:
        # log or re-raise as needed
        print("Error saving download metadata:", e)
    finally:
        conn.close()


def _ensure_token_table_exists():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS download_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            transaction_id INTEGER,
            file_path TEXT,
            format_type TEXT,
            created_at TEXT,
            expires_at TEXT,
            uses INTEGER DEFAULT 0,
            max_uses INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        )
        """
    )
    conn.commit()
    conn.close()


def _ensure_activity_table_exists():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS download_activity (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transaction_id INTEGER,
            download_time TEXT,
            file_format TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        )
        """
    )
    conn.commit()
    conn.close()


def create_download_token(user_id: int, transaction_id: int, file_path: str, format_type: str, ttl_seconds: int = 3600):
    import uuid

    _ensure_token_table_exists()
    token = uuid.uuid4().hex
    now = datetime.now()
    expires_at = now + timedelta(seconds=ttl_seconds)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO download_tokens (token, user_id, transaction_id, file_path, format_type, created_at, expires_at, uses, max_uses)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            token,
            user_id,
            transaction_id,
            file_path,
            format_type.upper(),
            now.isoformat(),
            expires_at.isoformat(),
            0,
            1,
        ),
    )
    conn.commit()
    conn.close()
    return token


def validate_download_token(token: str, user_id: int = None):
    _ensure_token_table_exists()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM download_tokens WHERE token = ?", (token,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Invalid token"

    if user_id is not None and row["user_id"] != user_id:
        conn.close()
        return False, "Token does not belong to user"

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now() > expires_at:
        conn.close()
        return False, "Token expired"

    if row["uses"] >= row["max_uses"]:
        conn.close()
        return False, "Token already used"

    # increment uses
    cursor.execute(
        "UPDATE download_tokens SET uses = uses + 1 WHERE token = ?",
        (token,),
    )
    conn.commit()
    conn.close()

    return True, dict(row)


def cleanup_expired_tokens():
    _ensure_token_table_exists()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM download_tokens WHERE expires_at < ?", (datetime.now().isoformat(),))
    conn.commit()
    conn.close()


def log_download_activity(user_id: int, transaction_id: int, file_format: str, ip_address: str = None):
    _ensure_activity_table_exists()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO download_activity (user_id, transaction_id, download_time, file_format, ip_address) VALUES (?, ?, ?, ?, ?)",
        (user_id, transaction_id, datetime.now().isoformat(), file_format, ip_address),
    )
    conn.commit()
    conn.close()


def generate_comparison_image(original_pil, cartoon_pil, output_path):
    # Convert both to RGB mode to avoid mode mismatch (e.g., RGBA, L)
    orig = original_pil.convert("RGB")
    cart = cartoon_pil.convert("RGB")
    width = orig.width + cart.width
    height = max(orig.height, cart.height)
    combo = Image.new("RGB", (width, height), (255, 255, 255))
    combo.paste(orig, (0, 0))
    combo.paste(cart, (orig.width, 0))
    combo.save(output_path, format="PNG")
    return output_path


def generate_receipt_pdf(user_id, transaction_id, order_id, amount, out_path):
    # Generate a simple text-based PDF via PIL because reportlab isn't available.
    from PIL import ImageFont, ImageDraw

    lines = [
        f"Receipt for Cartoonify Pro",
        f"User ID: {user_id}",
        f"Transaction ID: {transaction_id}",
        f"Order ID: {order_id}",
        f"Amount: ₹{amount/100:.2f}",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    # simple page size
    page_w, page_h = 595, 842
    img = Image.new("RGB", (page_w, page_h), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font = ImageFont.load_default()

    y = 80
    for line in lines:
        draw.text((50, y), line, fill="black", font=font)
        y += 25

    img.save(out_path, format="PDF", resolution=100.0)
    return out_path


def get_download_history(user_id, limit=100):
    _ensure_download_table_exists()
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ih.image_id, ih.filename, ih.style, ih.download_timestamp, t.payment_id as transaction_id
        FROM ImageHistory ih
        LEFT JOIN transactions t ON ih.user_id = t.user_id
        WHERE ih.user_id = ?
        ORDER BY ih.download_timestamp DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ---------------------------------------------------------------------------
# File management functions
# ---------------------------------------------------------------------------

def delete_old_files(folder: str = "output/downloads"):
    """Remove files older than 24 hours from the provided download folder.

    This is intended to be called periodically (for example on app startup or
    as part of a background maintenance callback).
    """
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    if not os.path.isdir(folder):
        return

    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                os.remove(fpath)
        except Exception:
            # ignore permissions or directory issues
            continue

# ---------------------------------------------------------------------------
# Image preparation for download
# ---------------------------------------------------------------------------

def _add_watermark(pil_img: Image.Image, text: str = "Preview - AI Cartoonify") -> Image.Image:
    """Return a new PIL image with a semi-transparent watermark in the
    bottom-right corner.
    """
    width, height = pil_img.size
    watermark = Image.new("RGBA", pil_img.size)
    drawing = ImageDraw.Draw(watermark)

    # choose a reasonable font size relative to image size
    font_size = max(12, width // 20)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # determine size of the text; account for Pillow versions
    try:
        text_width, text_height = drawing.textsize(text, font=font)
    except AttributeError:
        # textsize may be missing in some builds; fallback to font.getsize
        try:
            text_width, text_height = font.getsize(text)
        except Exception:
            # as a last resort use bbox
            bbox = drawing.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
    padding = 10
    position = (width - text_width - padding, height - text_height - padding)

    # draw text with transparency
    drawing.text(position, text, fill=(255, 255, 255, 120), font=font)

    combined = Image.alpha_composite(pil_img.convert("RGBA"), watermark)
    return combined.convert(pil_img.mode)


def prepare_image_for_download(
    image,
    user_id,
    image_id,
    style,
    original_filename,
    format_type="PNG",
    quality_mode="high",
    is_premium_user=False,
):
    """Save a transformed image to disk ready for user download.

    Parameters
    ----------
    image : PIL.Image or numpy array
        The processed cartoon image.
    user_id : int
        ID of the current user.
    image_id : int
        ID of the processed image (for metadata tracking).
    style : str
        Name or description of the style applied.
    original_filename : str
        The name of the image as uploaded by the user (used in new filename).
    format_type : str
        One of 'PNG', 'JPG', or 'PDF'.
    quality_mode : str
        Either 'high' or 'optimized'; adjusts compression/quality parameters.
    is_premium_user : bool
        If False, a watermark will be added to the image before saving.

    Returns
    -------
    dict
        success status and either path or error message.
    """
    # ensure output directory exists
    out_dir = os.path.join("output", "downloads")
    os.makedirs(out_dir, exist_ok=True)

    # convert image to PIL if needed
    try:
        import numpy as np
    except ImportError:
        np = None

    if np is not None and isinstance(image, np.ndarray):
        # convert numpy array directly
        try:
            image = Image.fromarray(np.uint8(image))
        except Exception:
            return {"success": False, "error": "Unsupported numpy array type"}
    elif isinstance(image, (list, tuple)):
        # plain list/tuple, assume file-like was already handled, else array
        try:
            import numpy as np

            image = Image.fromarray(np.uint8(image))
        except Exception:
            return {"success": False, "error": "Unsupported image type"}
    elif not isinstance(image, Image.Image):
        try:
            image = Image.open(image)
        except Exception as e:
            return {"success": False, "error": f"Cannot open image: {e}"}

    # watermark for non-premium users
    if not is_premium_user:
        try:
            image = _add_watermark(image)
        except Exception as e:
            # proceed but log
            print("Watermarking failed:", e)

    # create unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base = os.path.basename(original_filename)
    name, _ext = os.path.splitext(base)
    unique_name = f"{user_id}_{timestamp}_{name}"  # extension added later

    params = {}
    format_type = format_type.upper()
    if format_type == "JPG":
        params["quality"] = 95 if quality_mode == "high" else 70
        params["optimize"] = True
        ext = ".jpg"
        # PIL expects JPEG as format string
        format_type = "JPEG"
    elif format_type == "PDF":
        ext = ".pdf"
    else:  # default PNG
        # for png compression from 0 (no compression) to 9
        params["compress_level"] = 1 if quality_mode == "high" else 9
        ext = ".png"

    filename = unique_name + ext
    path = os.path.join(out_dir, filename)

    try:
        # special handling for PDF: PIL expects RGB
        if format_type == "PDF":
            image_rgb = image.convert("RGB")
            image_rgb.save(path, format="PDF", **params)
        else:
            image.save(path, format=format_type, **params)

        # update session state
        st.session_state["download_path"] = path

        # record metadata
        try:
            save_download_metadata(user_id, image_id, style, filename)
        except Exception:
            pass

        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}
