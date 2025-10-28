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
        exif = img._getexif()
        if exif:
            orientation_key = next((k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None)
            orientation = exif.get(orientation_key)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
        img.save(img_path)
    except Exception as e:
        print(f"[Orientation] ⚠️ {e}")


def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report,
                         save_path, weather_icon_path=None, safety_sheet_path=None):

    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Bold", fontName="Helvetica-Bold"))

    # === PAGE 1: Log Info ===
    if logo_path and os.path.exists(logo_path):
        fix_image_orientation(logo_path)
        elements.append(Image(logo_path, width=120, height=50))

    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    for key in ["project_name", "date", "location", "weather"]:
        if key in data:
            elements.append(Paragraph(f"<b>{key.capitalize()}:</b> {data[key]}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    for section in ["work_done", "crew_notes", "safety_notes"]:
        if section in data and data[section].strip():
            elements.append(Paragraph(f"<b>{section.replace('_',' ').title()}:</b>", styles["Bold"]))
            elements.append(Paragraph(data[section], styles["Normal"]))
            elements.append(Spacer(1, 12))

    elements.append(PageBreak())

    # === PAGE 2: Photos ===
    if image_paths:
        elements.append(Paragraph("<b>Job Site Photos</b>", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        photo_rows, row = [], []

        for idx, path in enumerate(image_paths):
            if os.path.exists(path):
                fix_image_orientation(path)
                row.append(Image(path, width=250, height=150))
                if len(row) == 2:
                    photo_rows.append(row)
                    row = []
                if len(photo_rows) == 3:
                    elements.append(Table(photo_rows, colWidths=[270, 270]))
                    elements.append(PageBreak())
                    photo_rows = []

        if row:
            photo_rows.append(row)
        if photo_rows:
            elements.append(Table(photo_rows, colWidths=[270, 270]))
            elements.append(PageBreak())

    # === PAGE 3: AI Analysis ===
    elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    completion = progress_report.get("completion", 0)
    user_override = progress_report.get("user_override", False)
    note = " (user adjusted)" if user_override else ""
    try:
        percent = int(round(float(completion)))
    except:
        percent = 0

    elements.append(Paragraph(f"<b>Completion:</b> {percent}%{note}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    if ai_analysis:
        for item in ai_analysis.get("scored_items", []):
            label = item.get("scope", "")
            score = int(round(item.get("confidence", 0)))
            icon = "✅" if item.get("match") else "❌"
            elements.append(Paragraph(f"{icon} {label} – {score}%", styles["Normal"]))
        elements.append(Spacer(1, 12))

        out_items = ai_analysis.get("out_of_scope", [])
        valid = [line for line in out_items if len(line.split()) > 4]
        if valid:
            elements.append(Paragraph("<b>Out-of-Scope Items:</b>", styles["Bold"]))
            for line in valid:
                elements.append(Paragraph(f"• {line}", styles["Normal"]))

    elements.append(PageBreak())

    # === PAGE 4: Safety Sheet ===
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("<b>Safety Sheet</b>", styles["Heading2"]))
        if safety_sheet_path.endswith(".pdf"):
            try:
                reader = PdfReader(safety_sheet_path)
                for page in reader.pages:
                    text = page.extract_text() or "Page unreadable"
                    elements.append(Paragraph(text, styles["Normal"]))
            except Exception as e:
                elements.append(Paragraph(f"Error reading safety sheet: {e}", styles["Normal"]))
        elif safety_sheet_path.lower().endswith((".jpg", ".jpeg", ".png")):
            fix_image_orientation(safety_sheet_path)
            elements.append(Image(safety_sheet_path, width=500, height=350))

    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)


def _footer(canvas: Canvas, doc):
    footer_text = "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm"
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(30, 30, footer_text)
    canvas.drawRightString(letter[0] - 30, 30, f"Page {doc.page}")
    canvas.restoreState()
