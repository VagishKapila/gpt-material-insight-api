# pdf_generator.py — Full, Clean Version with Debug Comments

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as PlatypusImage, Paragraph, SimpleDocTemplate, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfMerger
from PIL import Image
import os
import io

def create_daily_log_pdf(data, image_paths, logo_path=None, ai_analysis=None, progress_report=None, save_path='output.pdf', weather_icon_path=None, safety_sheet_path=None):
    print("[DEBUG] Starting PDF generation")

    styles = getSampleStyleSheet()
    centered = ParagraphStyle(name='centered', parent=styles['Heading2'], alignment=TA_CENTER)
    story = []

    # Page 1 – Header
    print("[DEBUG] Creating Page 1")
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    if logo_path and os.path.exists(logo_path):
        story.append(PlatypusImage(logo_path, width=150, height=60))
    story.append(Paragraph("DAILY LOG", centered))
    story.append(Spacer(1, 12))

    fields = [
        ("Project Name", data.get("project_name", "")),
        ("Location", data.get("location", "")),
        ("Date", data.get("date", "")),
        ("Crew Notes", data.get("crew_notes", "")),
        ("Work Done", data.get("work_done", "")),
        ("Safety Notes", data.get("safety_notes", "")),
    ]

    for title, val in fields:
        story.append(Paragraph(f"<b>{title}:</b> {val}", styles["Normal"]))
        story.append(Spacer(1, 6))

    if weather_icon_path and os.path.exists(weather_icon_path):
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Weather:</b>", styles["Normal"]))
        story.append(PlatypusImage(weather_icon_path, width=50, height=50))

    story.append(PageBreak())

    # Page 2 – Images
    print("[DEBUG] Adding job site images")
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            if img.width > img.height:
                img = img.rotate(90, expand=True)
            img.thumbnail((500, 500))
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            story.append(PlatypusImage(buffer, width=img.width * 0.75, height=img.height * 0.75))
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"[ERROR] Failed to embed image {img_path}: {e}")

    story.append(PageBreak())

    # Page 3 – AI/Scope Analysis
    if ai_analysis or progress_report:
        print("[DEBUG] Adding AI/AR analysis page")
        story.append(Paragraph("<b>AI/AR Analysis</b>", styles["Heading2"]))
        story.append(Spacer(1, 12))
        if ai_analysis:
            story.append(Paragraph(f"<b>AI Notes:</b><br/>{ai_analysis}", styles["Normal"]))
            story.append(Spacer(1, 12))
        if progress_report:
            story.append(Paragraph(f"<b>Scope Progress:</b><br/>{progress_report}", styles["Normal"]))
            story.append(Spacer(1, 12))
        story.append(PageBreak())

    # Page 4 – Safety Sheet
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        ext = os.path.splitext(safety_sheet_path)[1].lower()
        print("[DEBUG] Adding safety sheet")
        if ext in ['.jpg', '.jpeg', '.png']:
            try:
                img = Image.open(safety_sheet_path)
                img.thumbnail((500, 700))
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                story.append(Paragraph("<b>Safety Sheet</b>", styles["Heading2"]))
                story.append(Spacer(1, 12))
                story.append(PlatypusImage(buffer, width=img.width * 0.75, height=img.height * 0.75))
            except Exception as e:
                print(f"[ERROR] Failed to render safety image: {e}")
        elif ext == '.pdf':
            try:
                doc.build(story)
                merger = PdfMerger()
                merger.append(save_path)
                merger.append(safety_sheet_path)
                merger.write(save_path)
                merger.close()
                print("[DEBUG] PDF with attached safety PDF created")
                return
            except Exception as e:
                print(f"[ERROR] Failed to append safety PDF: {e}")
        else:
            print("[WARN] Unsupported safety sheet file format")

    print("[DEBUG] Finalizing PDF")
    doc.build(story)
