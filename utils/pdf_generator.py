import os
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
)
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage, ImageOps


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
    doc = SimpleDocTemplate(save_path, pagesize=LETTER)
    styles = getSampleStyleSheet()
    flowables = []

    # --- PAGE 1: Header ---
    flowables.append(Paragraph("<b>■ ■ DAILY LOG</b>", styles['Title']))
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
        flowables.append(Image(weather_icon_path, width=20, height=20))
        flowables.append(Spacer(1, 12))

    for note in ["crew_notes", "work_done", "safety_notes"]:
        flowables.append(Paragraph(f"<b>{note.replace('_', ' ').title()}</b>", styles['Heading4']))
        flowables.append(Paragraph(data.get(note, ""), styles['Normal']))
        flowables.append(Spacer(1, 12))

    flowables.append(Spacer(1, 30))
    flowables.append(Paragraph("<i>Powered by Nails & Notes</i>", styles['Normal']))

    flowables.append(PageBreak())

    # --- PAGE 2: Jobsite Photos ---
    if image_paths:
        flowables.append(Paragraph("<b>■ Job Site Photos</b>", styles['Heading3']))
        for image_path in image_paths:
            compressed_path = image_path.replace("uploads/", "compressed/")
            os.makedirs(os.path.dirname(compressed_path), exist_ok=True)
            compress_image(image_path, compressed_path)
            flowables.append(Image(compressed_path, width=320, height=240))
            flowables.append(Spacer(1, 8))

        flowables.append(PageBreak())

    # --- PAGE 3: AI Progress Report ---
    if ai_analysis and progress_report:
        flowables.append(Paragraph("<b>■ Scope Progress (AI Analyzed)</b>", styles['Heading3']))
        checklist = generate_progress_paragraph(progress_report)
        flowables.append(Paragraph(checklist, styles['Normal']))
        flowables.append(PageBreak())

    # --- PAGE 4: Safety Sheet Upload ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        flowables.append(Paragraph("<b>■ Safety Sheet</b>", styles['Heading3']))
        safety_ext = os.path.splitext(safety_sheet_path)[1].lower()
        if safety_ext in ['.jpg', '.jpeg', '.png']:
            flowables.append(Image(safety_sheet_path, width=400, height=300))

    doc.build(flowables)
    return save_path
