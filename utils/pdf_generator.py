import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

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

    # --- Title and Project Info ---
    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Project:</b> {data.get('project_name', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {data.get('date', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Location:</b> {data.get('location', '')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- Work Done ---
    elements.append(Paragraph("<b>Work Done:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("work_done", "N/A"), styles["Normal"]))
    elements.append(Spacer(1, 6))

    # --- Crew Notes ---
    elements.append(Paragraph("<b>Crew Notes:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("crew_notes", "N/A"), styles["Normal"]))
    elements.append(Spacer(1, 6))

    # --- Safety Notes ---
    elements.append(Paragraph("<b>Safety Notes:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("safety_notes", "N/A"), styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- AI Scope Analysis ---
    if ai_analysis:
        elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
        elements.append(Paragraph(f"Completion: {ai_analysis.get('completion', 0)}%", styles["Normal"]))
        elements.append(Spacer(1, 6))

        # Matched Items Table
        scored = ai_analysis.get("scored_items", [])
        if scored:
            table_data = [["Scope Item", "Confidence", "Match"]]
            for s in scored:
                table_data.append([
                    s["scope"][:70] + ("..." if len(s["scope"]) > 70 else ""),
                    f"{s['confidence']}",
                    "✅" if s["match"] else "❌"
                ])
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

        if ai_analysis.get("out_of_scope"):
            elements.append(Paragraph("<b>Out-of-Scope Items:</b>", styles["Heading3"]))
            for line in ai_analysis["out_of_scope"]:
                elements.append(Paragraph(line, styles["Normal"]))
            elements.append(Spacer(1, 12))

    # --- Job Photos ---
    if image_paths:
        elements.append(Paragraph("<b>Job Site Photos</b>", styles["Heading2"]))
        for path in image_paths:
            if os.path.exists(path):
                elements.append(Image(path, width=240, height=180))
                elements.append(Spacer(1, 6))

    # --- Safety Sheet Info ---
    if safety_sheet_path:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Safety Sheet:</b> {os.path.basename(safety_sheet_path)}", styles["Normal"]))

    # --- Footer ---
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Confidential – Do Not Duplicate without written consent from BAINS Dev Comm", styles["Normal"]))

    doc.build(elements)
    print(f"✅ PDF successfully created at {save_path}")
