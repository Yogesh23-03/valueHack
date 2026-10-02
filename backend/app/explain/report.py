from reportlab.pdfgen import canvas
import io

def generate_report():
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "BizSim Decision Report")
    c.drawString(100, 700, "Situation: Supplier delay")
    c.drawString(100, 650, "Recommended Action: Combined")
    c.save()
    buf.seek(0)
    return buf
