import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from PyPDF2 import PdfReader
from PIL import Image as PILImage, ExifTags

def fix_image_orientation(img_path):
    try:
        img = PILImage.open(img_path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
            img.save(img_path)
            img.close()
    except Exception as e:
        print(f"Orientation fix failed: {e}")

def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report,
                         save_path, weather_icon_path=None, safety_sheet_path=None):
    
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Bold', fontName='Helvetica-Bold'))

    # --- Page 1: Header, Info, Notes ---
    if logo_path and os.path.exists(logo_path):
        fix_image_orientation(logo_path)
        elements.append(Image(logo_path, width=120, height=50))
    
    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    for key in ["Project", "Date", "Location", "Weather"]:
        if key in data:
            elements.append(Paragraph(f"<b>{key}:</b> {data[key]}", styles["Normal"]))

    elements.append(Spacer(1, 12))

    for section in ["Work Done", "Crew Notes", "Safety Notes"]:
        if section in data and data[section].strip():
            elements.append(Paragraph(f"<b>{section}:</b>", styles["Bold"]))
            elements.append(Paragraph(data[section], styles["Normal"]))
            elements.append(Spacer(1, 12))

    elements.append(PageBreak())

    # --- Page 2: Jobsite Photos ---
    elements.append(Paragraph("<b>Job Site Photos</b>", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    photo_cells = []
    for idx, path in enumerate(image_paths):
        if os.path.exists(path):
            fix_image_orientation(path)
            photo_cells.append(Image(path, width=250, height=150))
            if len(photo_cells) == 2:
                elements.append(Table([photo_cells], colWidths=[270, 270]))
                elements.append(Spacer(1, 12))
                photo_cells = []

    if photo_cells:
        elements.append(Table([photo_cells], colWidths=[270] * len(photo_cells)))
        elements.append(Spacer(1, 12))

    elements.append(PageBreak())

    # --- Page 3: AI Scope Analysis ---
    elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    if isinstance(progress_report, dict):
        percent = progress_report.get("completion", 0)
        try:
            percent = round(float(percent), 1)
            elements.append(Paragraph(f"<b>Completion:</b> {percent}%", styles["Normal"]))
            elements.append(Spacer(1, 12))
        except Exception:
            elements.append(Paragraph("<b>Completion:</b> N/A", styles["Normal"]))

        scored_items = progress_report.get("scored_items", [])
        if scored_items:
            for item in scored_items:
                confidence = item.get("confidence", "N/A")
                label = item.get("scope", "")
                try:
                    conf_value = round(float(confidence), 1)
                except Exception:
                    conf_value = "N/A"
                elements.append(Paragraph(f"• {label} – {conf_value}%", styles["Normal"]))
            elements.append(Spacer(1, 8))

        out_items = progress_report.get("out_of_scope", [])
        if out_items:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<b>Out-of-Scope Items:</b>", styles["Bold"]))
            for line in out_items:
                elements.append(Paragraph(f"• {line}", styles["Normal"]))

    elements.append(PageBreak())

    # --- Page 4: Safety Sheet ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("<b>Safety Sheet</b>", styles["Heading2"]))
        if safety_sheet_path.endswith(".pdf"):
            try:
                reader = PdfReader(safety_sheet_path)
                for page in reader.pages:
                    text = page.extract_text()
                    elements.append(Paragraph(text or "[Unreadable Page]", styles["Normal"]))
            except Exception as e:
                elements.append(Paragraph(f"Error loading safety sheet PDF: {e}", styles["Normal"]))
        elif safety_sheet_path.lower().endswith((".jpg", ".jpeg", ".png")):
            fix_image_orientation(safety_sheet_path)
            elements.append(Image(safety_sheet_path, width=500, height=350))

    # --- Final build ---
    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)

def _footer(canvas: Canvas, doc):
    footer_text = "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm"
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(30, 30, footer_text)
    canvas.drawRightString(letter[0] - 30, 30, f"Page {doc.page}")
    canvas.restoreState()
