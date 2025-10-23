import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Image as PlatypusImage
)
from reportlab.pdfgen import canvas
from PyPDF2 import PdfMerger
from PIL import Image, ExifTags


def auto_rotate_image(path):
    try:
        img = Image.open(path)
        for orientation in ExifTags.TAGS:
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
            img.save(path)
    except Exception:
        pass


def create_daily_log_pdf(data, image_paths, logo_path=None, ai_analysis="", scope_progress="", save_path="daily_log.pdf"):
    temp_log_pdf = "temp_log.pdf"
    temp_photo_pdf = "temp_photos.pdf"
    temp_analysis_pdf = "temp_analysis.pdf"

    styles = getSampleStyleSheet()
    story = []

    # 🛠️ PAGE 1: Daily Log
    story.append(Paragraph("<b>🛠️ DAILY LOG</b>", styles['Title']))
    story.append(Spacer(1, 12))

    if logo_path:
        try:
            logo_img = PlatypusImage(logo_path, width=120, height=50)
            story.append(logo_img)
            story.append(Spacer(1, 12))
        except:
            pass

    # Project Metadata
    for field in ["project_name", "location", "date", "weather"]:
        label = field.replace("_", " ").title()
        story.append(Paragraph(f"<b>{label}:</b> {data.get(field, '')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Notes Section
    for field in ["crew_notes", "work_done", "safety_notes"]:
        label = field.replace("_", " ").title()
        story.append(Paragraph(f"<b>{label}</b>", styles['Heading4']))
        story.append(Paragraph(data.get(field, ""), styles['Normal']))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Powered by Nails & Notes</i>", styles['Normal']))

    doc = SimpleDocTemplate(temp_log_pdf, pagesize=A4)
    doc.build(story)

    # 📸 PAGE 2: Photos
    c = canvas.Canvas(temp_photo_pdf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "📸 Job Site Photos")

    x, y = 40, 750
    img_count = 0
    page_num = 2

    for path in image_paths[:20]:
        try:
            auto_rotate_image(path)  # Fix orientation before drawing
            img = ImageReader(path)
            c.drawImage(img, x, y, width=240, height=180, preserveAspectRatio=True)
            x += 270
            if x > 500:
                x = 40
                y -= 200
            if y < 100:
                c.setFont("Helvetica", 10)
                c.drawRightString(580, 20, f"Page {page_num}")
                c.showPage()
                c.setFont("Helvetica-Bold", 16)
                c.drawString(40, 800, "📸 Continued")
                x, y = 40, 750
                page_num += 1
            img_count += 1
        except:
            continue

    if img_count:
        c.setFont("Helvetica", 10)
        c.drawRightString(580, 20, f"Page {page_num}")
        c.save()
    else:
        open(temp_photo_pdf, 'w').close()

    # 🤖 PAGE 3: AI + Scope
    include_analysis = ai_analysis.strip() or scope_progress.strip()
    if include_analysis:
        c = canvas.Canvas(temp_analysis_pdf, pagesize=A4)
        page_num += 1
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, 800, "🤖 AI/AR Analysis")
        c.setFont("Helvetica", 12)

        y = 780
        for line in ai_analysis.splitlines():
            c.drawString(40, y, line)
            y -= 16
            if y < 60:
                c.showPage()
                y = 800

        if scope_progress.strip():
            c.setFont("Helvetica-Bold", 16)
            y -= 20
            c.drawString(40, y, "📋 Scope Progress Tracker")
            c.setFont("Helvetica", 12)
            y -= 20
            for line in scope_progress.splitlines():
                if y < 60:
                    c.showPage()
                    y = 800
                c.drawString(40, y, line)
                y -= 16

        # Final footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(A4[0]/2, 30, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
        c.setFont("Helvetica", 10)
        c.drawRightString(580, 20, f"Page {page_num}")
        c.save()
    else:
        open(temp_analysis_pdf, 'w').close()

    # ✅ Merge all pages
    merger = PdfMerger()
    merger.append(temp_log_pdf)
    if os.path.getsize(temp_photo_pdf) > 0:
        merger.append(temp_photo_pdf)
    if os.path.getsize(temp_analysis_pdf) > 0:
        merger.append(temp_analysis_pdf)
    merger.write(save_path)
    merger.close()

    # 🧹 Cleanup
    for f in [temp_log_pdf, temp_photo_pdf, temp_analysis_pdf]:
        try:
            os.remove(f)
        except:
            pass

    return save_path
