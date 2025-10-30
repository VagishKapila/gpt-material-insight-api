# utils/pdf_generator.py

import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

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

    # --- Page 1: Metadata ---
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=50))
    elements.append(Paragraph("<b>DAILY LOG REPORT</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    for label, val in {
        "Project Name": data.get("project_name", "—"),
        "Client Name": data.get("client_name", "—"),
        "Location": data.get("location", "—"),
        "Date": data.get("date", "—"),
        "Weather": data.get("weather", "—")
    }.items():
        elements.append(Paragraph(f"<b>{label}:</b> {val}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    for label, val in {
        "Work Done": data.get("work_done", "—"),
        "Crew Notes": data.get("crew_notes", "—"),
        "Safety Notes": data.get("safety_notes", "—")
    }.items():
        elements.append(Paragraph(f"<b>{label}:</b><br/>{val}", styles["Normal"]))
        elements.append(Spacer(1, 8))

    elements.append(PageBreak())

    # --- Page 2: Jobsite Photos ---
    elements.append(Paragraph("<b>📸 Job Site Photos</b>", styles["Heading2"]))
    table_data = []
    row = []
    for i, img_path in enumerate(image_paths):
        try:
            compressed = fix_orientation_and_compress(img_path)
            img = Image(compressed, width=2.5*inch, height=2.5*inch)
            row.append(img)
            if len(row) == 2:
                table_data.append(row)
                row = []
        except Exception as e:
            print(f"Failed to add photo {img_path}: {e}")
    if row:
        table_data.append(row)
    if table_data:
        table = Table(table_data, hAlign='LEFT')
        table.setStyle(TableStyle([("BOTTOMPADDING", (0,0), (-1,-1), 12)]))
        elements.append(table)
    else:
        elements.append(Paragraph("No photos uploaded.", styles["Normal"]))
    elements.append(PageBreak())

    # --- Page 3: AI Analysis ---
    elements.append(Paragraph("<b>🤖 AI Scope Analysis</b>", styles["Heading2"]))
    completion = ai_analysis.get("completion", 0)
    elements.append(Paragraph(f"<b>Estimated Completion:</b> {completion}%", styles["Normal"]))
    elements.append(Spacer(1, 10))

    scored_items = ai_analysis.get("scored_items", [])
    for item in scored_items:
        scope_text = item.get("scope", "")
        confidence = item.get("confidence", 0)
        match = item.get("match", False)
        img = item.get("matched_image", "(No match found)")
        mark = "✅" if match else "❌"
        line = f"{mark} <b>{scope_text}</b><br/>Confidence: {confidence}%"
        if img:
            line += f"<br/>Matched Image: <i>{img}</i>"
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 6))

    out = ai_analysis.get("out_of_scope", [])
    if out:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<b>⚠️ Out-of-Scope Items:</b>", styles["Heading3"]))
        for line in out:
            if len(line.strip()) > 4:
                elements.append(Paragraph(f"• {line}", styles["Normal"]))

    elements.append(PageBreak())

    # --- Page 4: Safety Sheet ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        try:
            if safety_sheet_path.lower().endswith(".pdf"):
                elements.append(Paragraph("<b>Safety Sheet (PDF Attached Separately)</b>", styles["Normal"]))
            else:
                elements.append(Paragraph("<b>Safety Sheet</b>", styles["Heading2"]))
                img = fix_orientation_and_compress(safety_sheet_path)
                elements.append(Image(img, width=400, height=400))
        except Exception as e:
            elements.append(Paragraph(f"❌ Failed to add safety sheet: {e}", styles["Normal"]))

    doc.build(elements)
