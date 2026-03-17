import io

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_pdf_receipt(order_id, payment_id, amount, timestamp, user, is_proforma=False):
    """Return a BytesIO containing a styled PDF receipt/invoice."""
    if not HAS_REPORTLAB:
        return None

    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Background
    c.setFillColor(colors.HexColor("#0F0F1A"))
    c.rect(0, 0, w, h, fill=True, stroke=False)

    # Top accent
    c.setFillColor(colors.HexColor("#6C63FF"))
    c.rect(0, h - 18 * mm, w, 18 * mm, fill=True, stroke=False)
    for i, col in enumerate(["#6C63FF", "#7B74FF", "#8A85FF", "#9996FF"]):
        c.setFillColor(colors.HexColor(col))
        c.rect(0, h - (18 + i * 1.5) * mm, w, 1.5 * mm, fill=True, stroke=False)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 12 * mm, "TOONIFY PRO" if not is_proforma else "TOONIFY PRO")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#B0B8FF"))
    c.drawCentredString(w / 2, h - 24 * mm, "Official Payment Receipt" if not is_proforma else "Pro-forma Invoice")

    # Badge
    badge_y = h - 44 * mm
    c.setFillColor(colors.HexColor("#1A2A1A"))
    c.roundRect(w / 2 - 55, badge_y, 110, 14 * mm, 7, fill=True, stroke=False)
    
    if is_proforma:
        c.setFillColor(colors.HexColor("#F9CA74"))
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(w / 2, badge_y + 4 * mm, "PENDING PAYMENT")
    else:
        c.setFillColor(colors.HexColor("#48C9B0"))
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(w / 2, badge_y + 4 * mm, "PAYMENT SUCCESSFUL")

    c.setStrokeColor(colors.HexColor("#2A2A4A"))
    c.setLineWidth(1)
    c.line(20 * mm, h - 56 * mm, w - 20 * mm, h - 56 * mm)

    # Details
    details = [
        ("Date & Time",  timestamp),
        ("Order ID",     order_id),
        ("Payment ID",   payment_id if not is_proforma else "Pending"),
        ("Amount Due" if is_proforma else "Amount Paid",  f"INR {amount}"),
        ("Status",       "PENDING" if is_proforma else "SUCCESS"),
        ("Customer",     user),
        ("Product",      "Cartoon Image - HD Download"),
    ]
    row_h   = 12 * mm
    start_y = h - 64 * mm
    for i, (label, value) in enumerate(details):
        y = start_y - i * row_h
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#16162A"))
            c.rect(18 * mm, y - 3 * mm, w - 36 * mm, row_h, fill=True, stroke=False)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#9999CC"))
        c.drawString(22 * mm, y + 3 * mm, label.upper())
        c.setFont("Helvetica", 10)
        if label == "Status":
            c.setFillColor(colors.HexColor("#48C9B0"))
        elif label == "Amount Paid":
            c.setFillColor(colors.HexColor("#F9CA74"))
        else:
            c.setFillColor(colors.white)
        c.drawRightString(w - 22 * mm, y + 3 * mm, str(value))

    bottom_y = start_y - len(details) * row_h - 6 * mm
    c.setStrokeColor(colors.HexColor("#2A2A4A"))
    c.line(20 * mm, bottom_y, w - 20 * mm, bottom_y)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#6666AA"))
    c.drawCentredString(w / 2, bottom_y - 8 * mm,
                        "This is a computer-generated receipt and requires no signature.")
    c.drawCentredString(w / 2, bottom_y - 14 * mm,
                        "For support, contact support@toonifypro.com")

    c.setFillColor(colors.HexColor("#6C63FF"))
    c.rect(0, 0, w, 8 * mm, fill=True, stroke=False)

    c.save()
    buf.seek(0)
    return buf
