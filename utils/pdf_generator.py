import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfReader

def fix_orientation_and_compress(image_path):
    try:
        img = PILImage.open(image_path)
        img = img.convert("RGB")
        img.thumbnail((800, 800))
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        return temp_path
    except Exception:
        return image_path

def create_daily_log_pdf(
    data,
    image_paths,
    logo_path,
    ai_analysis,
    progress_report,
    save_path,
    weather_icon_path=None,
    safety_sheet_path=None
):
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    def header_footer(canvas, doc):
        canvas.saveState()
        footer = "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm"
        canvas.setFont("Helvetica", 9)
        canvas.drawString(inch, 0.5 * inch, footer)
        canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.restoreState()

    # --- Page 1: Basic Info ---
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=50))

    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    def add_paragraph(label, value):
        text = f"<b>{label}:</b> {value or '—'}"
        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 6))

    add_paragraph("Project Name", data.get("project_name"))
    add_paragraph("Client Name", data.get("client_name"))
    add_paragraph("Location", data.get("location"))
    add_paragraph("Date", data.get("date"))
    add_paragraph("Weather", data.get("weather"))

    elements.append(Spacer(1, 10))
    add_paragraph("Work Done", data.get("work_done"))
    add_paragraph("Crew Notes", data.get("crew_notes"))
    add_paragraph("Safety Notes", data.get("safety_notes"))

    elements.append(PageBreak())

    # --- Page 2: Photos ---
    if image_paths:
        elements.append(Paragraph("<b>📷 Job Site Photos</b>", styles["Heading2"]))
        photo_table = []
        row = []

        for i, img_path in enumerate(image_paths):
            compressed = fix_orientation_and_compress(img_path)
            img = Image(compressed, width=3*inch, height=2.25*inch)
            row.append(img)
            if len(row) == 2:
                photo_table.append(row)
                row = []

        if row:
            photo_table.append(row)

        table = Table(photo_table, hAlign="LEFT", colWidths=[3.1*inch]*2)
        elements.append(table)
        elements.append(PageBreak())

    # --- Page 3: AI Scope Analysis ---
    if ai_analysis:
        elements.append(Paragraph("<b>🤖 AI Scope Analysis</b>", styles["Heading2"]))
        completion = ai_analysis.get("completion", 0)
        elements.append(Paragraph(f"<b>Estimated Completion:</b> {completion}%", styles["Normal"]))
        elements.append(Spacer(1, 10))

        scored_items = ai_analysis.get("scored_items", [])
        for item in scored_items:
            label = "✅" if item.get("match") else "❌"
            text = f"{label} <b>{item.get('scope')}</b> — Confidence: {item.get('confidence')}%"
            elements.append(Paragraph(text, styles["Normal"]))
            elements.append(Spacer(1, 4))

        out_of_scope = ai_analysis.get("out_of_scope", [])
        if out_of_scope:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<b>🚨 Out-of-Scope Items:</b>", styles["Heading3"]))
            for line in out_of_scope:
                elements.append(Paragraph(f"- {line}", styles["Normal"]))
                elements.append(Spacer(1, 2))

        elements.append(PageBreak())

    # --- Page 4: Safety Sheet ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        ext = os.path.splitext(safety_sheet_path)[1].lower()
        elements.append(Paragraph("<b>📄 Safety Sheet</b>", styles["Heading2"]))
        if ext in [".jpg", ".jpeg", ".png"]:
            img = fix_orientation_and_compress(safety_sheet_path)
            elements.append(Image(img, width=6*inch, height=7*inch))
        elif ext == ".pdf":
            try:
                reader = PdfReader(safety_sheet_path)
                page = reader.pages[0]
                text = page.extract_text()
                for line in text.splitlines():
                    elements.append(Paragraph(line, styles["Normal"]))
            except Exception:
                elements.append(Paragraph("⚠️ Unable to read PDF safety sheet.", styles["Normal"]))

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)
