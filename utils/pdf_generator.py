from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image
import os
import io

def compress_image(image_path, quality=20):
    """Compress image using PIL and return a BytesIO object"""
    img = Image.open(image_path)
    img = img.convert("RGB")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)
    return buffer

def create_daily_log_pdf(project_name, date, weather, crew_notes, work_done, safety_notes, equipment, logo_path, photo_paths, include_page_2=True):
    filename = f"{project_name.replace(' ', '_')}_{date}.pdf"
    output_path = os.path.join("static", "generated", filename)

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # --- HEADER ---
    if logo_path:
        try:
            c.drawImage(logo_path, 50, height - 100, width=120, preserveAspectRatio=True, mask='auto')
        except:
            pass
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.darkblue)
    c.drawString(200, height - 60, "DAILY LOG REPORT")

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(50, height - 130, f"Project: {project_name}")
    c.drawString(50, height - 150, f"Date: {date}")
    c.drawString(50, height - 170, f"Weather: {weather}")

    # --- SECTION 1: CREW NOTES ---
    y = height - 210
    sections = [
        ("Crew Notes", crew_notes),
        ("Work Done", work_done),
        ("Safety Notes", safety_notes),
        ("Equipment Used", equipment)
    ]

    for title, content in sections:
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        c.drawString(50, y, title)
        y -= 20
        c.setFont("Helvetica", 12)
        text_obj = c.beginText(50, y)
        text_obj.textLines(content)
        c.drawText(text_obj)
        y -= 80

    # --- PAGE 2: PHOTOS ---
    if include_page_2 and photo_paths:
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "Job Site Photos")

        x, y = 50, height - 120
        max_width = 200
        max_height = 150
        spacing_x = 240
        spacing_y = 170
        photos_per_row = 2

        for i, path in enumerate(photo_paths):
            try:
                img_buffer = compress_image(path, quality=20)
                img = ImageReader(img_buffer)
                c.drawImage(img, x, y, width=max_width, height=max_height, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print("[IMAGE ERROR]", e)

            if (i + 1) % photos_per_row == 0:
                x = 50
                y -= spacing_y
            else:
                x += spacing_x

    c.save()
    return filename
