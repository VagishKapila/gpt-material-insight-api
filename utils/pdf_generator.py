import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
)
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage, ImageOps
from PyPDF2 import PdfReader


def compress_image(input_path, output_path, max_width=720, quality=60):
    with PILImage.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        width_percent = max_width / float(img.size[0])
        height = int(float(img.size[1]) * float(width_percent))
        img = img.resize((max_width, height), PILImage.Resampling.LANCZOS)
        img.save(output_path, "JPEG", quality=quality, optimize=True)


def get_weather_icon_path(weather_desc):
    if "sun" in weather_desc.lower():
        return "static/icons/sun.png"
    elif "cloud" in weather_desc.lower():
        return "static/icons/cloud.png"
    elif "rain" in weather_desc.lower():
        return "static/icons/rain.png"
    return None


def generate_progress_paragraph(progress_items):
    checklist = ""
    for item in progress_items:
        status = item.get("status", "").lower()
        symbol = {"done": "✓", "in-progress": "⏳", "pending": "❌"}.get(status, "•")
        checklist += f"{symbol} {item['task']}<br/>"
    return checklist


def create_daily_log_pdf(
    data,
    image_paths,
    logo_path=None,
    save_path="daily_log.pdf",
    ai_analysis=False,
    progress_report=None,
    weather_icon_path=None,
    safety_sheet_path=None
):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Checklist', leading=18, fontSize=11))
    flowables = []

    def footer(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawRightString(7.5 * inch, 0.5 * inch,
                                   f"Confidential – Do Not Duplicate without written consent from BAINS Dev Comm | Page {doc.page}")
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(save_path, pagesize=LETTER)
    doc.build_on = lambda *args, **kwargs: None  # prevent multi-page duplicate footer

    # --- PAGE 1: Daily Log ---
    if logo_path and os.path.exists(logo_path):
        flowables.append(Image(logo_path, width=100, height=40))

    flowables.append(Paragraph("<b>■ DAILY LOG</b>", styles['Title']))
    flowables.append(Spacer(1, 12))

    project_info = f"""
    <b>Project Name:</b> {data['project_name']}<br/>
    <b>Location:</b> {data['location']}<br/>
    <b>Date:</b> {data['date']}<br/>
    <b>Weather:</b> {data['weather']}
    """
    flowables.append(Paragraph(project_info, styles['Normal']))
    flowables.append(Spacer(1, 6))

    if weather_icon_path and os.path.exists(weather_icon_path):
        flowables.append(Image(weather_icon_path, width=30, height=30))
        flowables.append(Spacer(1, 12))

    for note in ["crew_notes", "work_done", "safety_notes"]:
        flowables.append(Paragraph(f"<b>{note.replace('_', ' ').title()}</b>", styles['Heading4']))
        flowables.append(Paragraph(data.get(note, ""), styles['Normal']))
        flowables.append(Spacer(1, 12))

    flowables.append(Spacer(1, 30))
    flowables.append(Paragraph("<i>Powered by Nails & Notes</i>", styles['Normal']))
    flowables.append(PageBreak())

    # --- PAGE 2: Job Site Photos ---
    if image_paths:
        flowables.append(Paragraph("<b>■ Job Site Photos</b>", styles['Heading3']))
        row = []
        count = 0
        for image_path in image_paths:
            compressed_path = image_path.replace("uploads/", "compressed/")
            os.makedirs(os.path.dirname(compressed_path), exist_ok=True)
            compress_image(image_path, compressed_path)
            img = Image(compressed_path, width=260, height=180)
            row.append(img)
            count += 1
            if count % 2 == 0:
                flowables.extend(row)
                flowables.append(Spacer(1, 12))
                row = []
        if row:
            flowables.extend(row)
        flowables.append(PageBreak())

    # --- PAGE 3: AI Scope Checklist ---
    if ai_analysis and progress_report:
        flowables.append(Paragraph("<b>■ Scope Progress (AI Analyzed)</b>", styles['Heading3']))
        checklist = generate_progress_paragraph(progress_report)
        flowables.append(Paragraph(checklist, styles['Checklist']))
        flowables.append(PageBreak())

    # --- PAGE 4: Safety Sheet ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        flowables.append(Paragraph("<b>■ Safety Sheet</b>", styles['Heading3']))
        ext = os.path.splitext(safety_sheet_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            flowables.append(Image(safety_sheet_path, width=480, height=360))
        elif ext == '.pdf':
            # Embed 1st page of PDF as image
            reader = PdfReader(safety_sheet_path)
            if len(reader.pages) > 0:
                from pdf2image import convert_from_path
                img = convert_from_path(safety_sheet_path, first_page=1, last_page=1)[0]
                img_path = safety_sheet_path.replace(".pdf", "_safety_preview.jpg")
                img.save(img_path, "JPEG")
                flowables.append(Image(img_path, width=480, height=360))

    doc.build(flowables, onFirstPage=footer, onLaterPages=footer)
    return save_path
