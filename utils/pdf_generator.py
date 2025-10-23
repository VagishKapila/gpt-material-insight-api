import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
)
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image as PILImage, ImageOps
from PyPDF2 import PdfReader


def compress_image(input_path, output_path, max_width=720, quality=60):
    """Compress and correct image orientation."""
    with PILImage.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        width_percent = max_width / float(img.size[0])
        height = int(float(img.size[1]) * float(width_percent))
        img = img.resize((max_width, height), PILImage.Resampling.LANCZOS)
        img.save(output_path, "JPEG", quality=quality, optimize=True)


def get_weather_icon_path(weather_desc):
    """Return local icon path for sun/cloud/rain based on weather text."""
    desc = weather_desc.lower()
    if "sun" in desc:
        return "static/icons/sun.png"
    elif "cloud" in desc:
        return "static/icons/cloud.png"
    elif "rain" in desc:
        return "static/icons/rain.png"
    return None


def generate_progress_paragraph(progress_items):
    """Render checklist view of scope progress."""
    if not progress_items:
        return "No scope progress detected."

    checklist = ""
    for item in progress_items:
        status = item.get("status", "").lower()
        symbol = {"done": "✅", "in-progress": "⏳", "pending": "❌"}.get(status, "•")
        task = item.get("task", "Unnamed task")
        checklist += f"{symbol} {task}<br/>"
    return checklist


def create_daily_log_pdf(
    data,
    image_paths,
    logo_path=None,
    save_path="daily_log.pdf",
    ai_analysis=False,
    scope_progress=None,
    weather_icon_path=None,
    safety_sheet_path=None
):
    """Generate full Daily Log PDF."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Checklist', leading=18, fontSize=11))
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, leading=20, spaceAfter=8, textColor=colors.darkblue))
    flowables = []

    # --- Footer ---
    def footer(canvas_obj, doc):
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawRightString(
            7.7 * inch, 0.5 * inch,
            f"Confidential – Do Not Duplicate without written consent from BAINS Dev Comm | Page {doc.page}"
        )
        canvas_obj.restoreState()

    doc = SimpleDocTemplate(save_path, pagesize=LETTER, topMargin=60, bottomMargin=40, leftMargin=50, rightMargin=50)

    # --- PAGE 1: DAILY LOG INFO ---
    if logo_path and os.path.exists(logo_path):
        flowables.append(Image(logo_path, width=120, height=50))
        flowables.append(Spacer(1, 12))

    flowables.append(Paragraph("■ DAILY LOG", styles['Title']))
    flowables.append(Spacer(1, 10))

    weather_icon = weather_icon_path if weather_icon_path and os.path.exists(weather_icon_path) else None

    info_data = [
        ["Project Name:", data.get("project_name", "")],
        ["Location:", data.get("location", "")],
        ["Date:", data.get("date", "")],
        ["Weather:", data.get("weather", "")]
    ]
    info_table = Table(info_data, colWidths=[100, 400])
    info_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
    ]))
    flowables.append(info_table)
    if weather_icon:
        flowables.append(Image(weather_icon, width=30, height=30))
    flowables.append(Spacer(1, 10))

    for note in ["crew_notes", "work_done", "safety_notes"]:
        flowables.append(Paragraph(f"<b>{note.replace('_', ' ').title()}</b>", styles['SectionHeader']))
        flowables.append(Paragraph(data.get(note, ""), styles['Normal']))
        flowables.append(Spacer(1, 12))

    flowables.append(Spacer(1, 30))
    flowables.append(Paragraph("<i>Powered by Nails & Notes</i>", styles['Normal']))
    flowables.append(PageBreak())

    # --- PAGE 2: JOB SITE PHOTOS ---
    if image_paths:
        flowables.append(Paragraph("■ Job Site Photos", styles['SectionHeader']))
        os.makedirs("static/compressed", exist_ok=True)

        row = []
        count = 0
        for image_path in image_paths:
            compressed_path = os.path.join("static/compressed", os.path.basename(image_path))
            compress_image(image_path, compressed_path)

            img = PILImage.open(compressed_path)
            img = ImageOps.exif_transpose(img)
            width, height = img.size
            aspect_ratio = width / height

            # landscape vs portrait
            if aspect_ratio > 1:
                img_width, img_height = 260, 180
            else:
                img_width, img_height = 180, 260

            img.save(compressed_path)
            flow_img = Image(compressed_path, width=img_width, height=img_height)
            row.append(flow_img)
            count += 1

            if count % 2 == 0:
                flowables.extend(row)
                flowables.append(Spacer(1, 12))
                row = []
        if row:
            flowables.extend(row)
        flowables.append(PageBreak())

    # --- PAGE 3: SCOPE PROGRESS (AI) ---
    if ai_analysis and scope_progress:
        flowables.append(Paragraph("■ Scope Progress (AI Analyzed)", styles['SectionHeader']))
        checklist_html = generate_progress_paragraph(scope_progress)
        flowables.append(Paragraph(checklist_html, styles['Checklist']))
        flowables.append(PageBreak())

    # --- PAGE 4: SAFETY SHEET ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        flowables.append(Paragraph("■ Safety Sheet", styles['SectionHeader']))
        ext = os.path.splitext(safety_sheet_path)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png']:
            flowables.append(Image(safety_sheet_path, width=480, height=360))
        elif ext == '.pdf':
            reader = PdfReader(safety_sheet_path)
            if len(reader.pages) > 0:
                from pdf2image import convert_from_path
                img = convert_from_path(safety_sheet_path, first_page=1, last_page=1)[0]
                img_path = safety_sheet_path.replace(".pdf", "_preview.jpg")
                img.save(img_path, "JPEG")
                flowables.append(Image(img_path, width=480, height=360))

    # --- BUILD ---
    doc.build(flowables, onFirstPage=footer, onLaterPages=footer)
    return save_path
