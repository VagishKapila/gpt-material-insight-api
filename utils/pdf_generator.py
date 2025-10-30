import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image as PILImage

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

    # PAGE 1: Header + Log Info
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=60))
    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Project:</b> {data.get('project_name', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Client:</b> {data.get('client_name', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Location:</b> {data.get('location', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {data.get('date', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Weather:</b> {data.get('weather', '')}", styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Work Performed:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("work_done", ""), styles["Normal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>Crew Notes:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("crew_notes", ""), styles["Normal"]))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>Safety Notes:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("safety_notes", ""), styles["Normal"]))
    elements.append(PageBreak())

    # PAGE 2: Photos Grid
    elements.append(Paragraph("<b>📸 Jobsite Photos</b>", styles["Heading2"]))
    photo_table = []
    row = []
    for idx, path in enumerate(image_paths):
        fixed_path = fix_orientation_and_compress(path)
        img = Image(fixed_path, width=3*inch, height=3*inch)
        row.append(img)
        if len(row) == 2:
            photo_table.append(row)
            row = []
    if row:
        photo_table.append(row)
    if photo_table:
        elements.append(Table(photo_table, colWidths=[3.2*inch]*2, hAlign="CENTER"))
    elements.append(PageBreak())

    # PAGE 3: AI Scope Analysis
    if ai_analysis:
        elements.append(Paragraph("🔍 AI Scope Analysis", styles["Heading2"]))
        completion = ai_analysis.get("completion", 0)
        elements.append(Paragraph(f"<b>Estimated Completion:</b> {round(completion, 1)}%", styles["Normal"]))
        elements.append(Spacer(1, 6))

        table_data = [["✔", "Scope Item", "Confidence", "Matched Image"]]
        for item in ai_analysis.get("scored_items", []):
            check = "✔" if item.get("match") else "❌"
            scope = item.get("scope", "")
            conf = f"{item.get('confidence', 0)}%"
            img = os.path.basename(item.get("matched_image", "")) if item.get("matched_image") else "-"
            table_data.append([check, scope, conf, img])

        table = Table(table_data, colWidths=[0.5*inch, 3.5*inch, 1.0*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "TOP")
        ]))
        elements.append(table)

        if ai_analysis.get("out_of_scope"):
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<b>⚠️ Out-of-Scope Items:</b>", styles["Heading3"]))
            for line in ai_analysis["out_of_scope"]:
                elements.append(Paragraph(f"• {line}", styles["Normal"]))
    elements.append(PageBreak())

    # PAGE 4: Safety Sheet
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("📋 Safety Sheet", styles["Heading2"]))
        try:
            fixed_path = fix_orientation_and_compress(safety_sheet_path)
            elements.append(Image(fixed_path, width=6*inch, height=7*inch))
        except Exception:
            elements.append(Paragraph("⚠️ Failed to display safety sheet", styles["Normal"]))

    # Footer
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(30, 20, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
        canvas.drawRightString(570, 20, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=footer, onLaterPages=footer)
