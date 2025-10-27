import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics import renderPDF


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

    # --- Logo ---
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=50))

    # --- Header Info ---
    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Project:</b> {data.get('project_name', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {data.get('date', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Location:</b> {data.get('location', '')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- Weather Icon ---
    if weather_icon_path and os.path.exists(weather_icon_path):
        elements.append(Image(weather_icon_path, width=40, height=40))
        elements.append(Spacer(1, 12))

    # --- Work/Crew/Safety Notes ---
    for label, key in [("Work Done", "work_done"), ("Crew Notes", "crew_notes"), ("Safety Notes", "safety_notes")]:
        elements.append(Paragraph(f"<b>{label}:</b>", styles["Heading3"]))
        elements.append(Paragraph(data.get(key, "N/A"), styles["Normal"]))
        elements.append(Spacer(1, 6))

    # --- AI Scope Analysis ---
    if ai_analysis:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
        completion = ai_analysis.get("completion", 0)

        # -- Visual Completion Bar --
        try:
            drawing = Drawing(200, 20)
            percent_width = 2 * completion  # scale
            drawing.add(Rect(0, 0, 200, 20, fillColor=colors.lightgrey))
            drawing.add(Rect(0, 0, percent_width, 20, fillColor=colors.green))
            elements.append(drawing)
            elements.append(Paragraph(f"<b>Completion:</b> {completion:.1f}%", styles["Normal"]))
        except Exception:
            elements.append(Paragraph(f"<b>Completion:</b> {completion:.1f}%", styles["Normal"]))

        elements.append(Spacer(1, 8))

        # -- Scored Items Table --
        scored = ai_analysis.get("scored_items", [])
        if scored:
            table_data = [["Scope Item", "Confidence", "Match"]]
            for s in scored:
                item = s.get("scope", "N/A")
                confidence = s.get("confidence", 0.0)
                is_match = s.get("match", False)
                table_data.append([
                    item[:75] + ("..." if len(item) > 75 else ""),
                    f"{confidence:.1f}%",
                    "✅" if is_match else "❌"
                ])
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

        # -- Out-of-Scope Items --
        oos = ai_analysis.get("out_of_scope", [])
        if oos:
            elements.append(Paragraph("<b>Out-of-Scope Items:</b>", styles["Heading3"]))
            for line in oos:
                elements.append(Paragraph(f"• {line}", styles["Normal"]))
            elements.append(Spacer(1, 12))

    # --- Job Site Photos ---
    if image_paths:
        elements.append(Paragraph("<b>Job Site Photos</b>", styles["Heading2"]))
        for path in image_paths:
            if os.path.exists(path):
                try:
                    elements.append(Image(path, width=240, height=180))
                    elements.append(Spacer(1, 6))
                except Exception:
                    continue

    # --- Safety Sheet Mention ---
    if safety_sheet_path:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Safety Sheet:</b> {os.path.basename(safety_sheet_path)}", styles["Normal"]))

    # --- Footer ---
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Confidential – Do Not Duplicate without written consent from BAINS Dev Comm", styles["Normal"]))

    try:
        doc.build(elements)
        print(f"✅ PDF successfully created at {save_path}")
    except Exception as e:
        print(f"❌ PDF creation failed: {e}")
