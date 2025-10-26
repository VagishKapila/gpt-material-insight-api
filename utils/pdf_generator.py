# ---- utils/pdf_generator.py ----
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

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
    """
    Generates the full Daily Log PDF (Page 1–4 layout).
    """
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # --- Title + Logo ---
    if logo_path:
        elements.append(Image(logo_path, width=100, height=50))
    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # --- Project Info ---
    elements.append(Paragraph(f"<b>Project:</b> {data.get('project_name', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {data.get('date', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Location:</b> {data.get('location', '')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- Work/Crew/Safety Notes ---
    elements.append(Paragraph("<b>Work Done:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("work_done", "N/A"), styles["Normal"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>Crew Notes:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("crew_notes", "N/A"), styles["Normal"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>Safety Notes:</b>", styles["Heading3"]))
    elements.append(Paragraph(data.get("safety_notes", "N/A"), styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- AI Analysis Section ---
    if ai_analysis:
        elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
        elements.append(Paragraph(f"Completion: {ai_analysis.get('completion', 0)}%", styles["Normal"]))
        elements.append(Spacer(1, 6))

        # Confidence Table
        scored = ai_analysis.get("scored_items", [])
        if scored:
            table_data = [["Scope Item", "Confidence", "Match"]]
            for s in scored:
                table_data.append([
                    s["scope"][:80] + ("..." if len(s["scope"]) > 80 else ""),
                    str(s["confidence"]),
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

        out_of_scope = ai_analysis.get("out_of_scope", [])
        if out_of_scope:
            elements.append(Paragraph("<b>Out of Scope Items:</b>", styles["Heading3"]))
            for line in out_of_scope:
                elements.append(Paragraph(line, styles["Normal"]))
            elements.append(Spacer(1, 12))

    # --- Job Photos ---
    if image_paths:
        elements.append(Paragraph("<b>Job Site Photos</b>", styles["Heading2"]))
        for img_path in image_paths:
            elements.append(Image(img_path, width=250, height=180))
            elements.append(Spacer(1, 6))

    # --- Safety Sheet ---
    if safety_sheet_path:
        elements.append(Paragraph("<b>Safety Sheet Uploaded:</b>", styles["Heading2"]))
        elements.append(Paragraph(os.path.basename(safety_sheet_path), styles["Normal"]))
        elements.append(Spacer(1, 12))

    # --- Footer ---
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm",
        styles["Normal"]
    ))

    # --- Build PDF ---
    doc.build(elements)
    print(f"✅ PDF successfully created at {save_path}")
