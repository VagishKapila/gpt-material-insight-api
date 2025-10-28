import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PyPDF2 import PdfReader

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
    for field in ["project_name", "client_name", "location", "date", "weather"]:
        val = data.get(field, "Not Provided")
        elements.append(Paragraph(f"<b>{field.replace('_', ' ').title()}:</b> {val}", styles["Normal"]))
        elements.append(Spacer(1, 6))

    # --- Section 1: Notes ---
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Work Done</b>", styles["Heading2"]))
    elements.append(Paragraph(data.get("work_done", ""), styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Crew Notes</b>", styles["Heading2"]))
    elements.append(Paragraph(data.get("crew_notes", ""), styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Safety Notes</b>", styles["Heading2"]))
    elements.append(Paragraph(data.get("safety_notes", ""), styles["Normal"]))
    elements.append(PageBreak())

    # --- Section 2: Jobsite Images (2 per row) ---
    if image_paths:
        elements.append(Paragraph("<b>Jobsite Photos</b>", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        row = []
        for i, img in enumerate(image_paths):
            if os.path.exists(img):
                row.append(Image(img, width=2.5*inch, height=2*inch))
                if len(row) == 2:
                    elements.append(Table([row], hAlign='LEFT', colWidths=[2.5*inch]*2))
                    elements.append(Spacer(1, 12))
                    row = []
        if row:
            elements.append(Table([row], hAlign='LEFT', colWidths=[2.5*inch]*2))
        elements.append(PageBreak())

    # --- Section 3: AI Analysis with Edited Scores ---
    if progress_report:
        elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
        elements.append(Spacer(1, 6))
        percent = int(round(progress_report.get("completion", 0)))
        elements.append(Paragraph(f"<b>Total Completion:</b> {percent}% (user-edited)", styles["Normal"]))
        elements.append(Spacer(1, 12))

        if "scored_items" in progress_report:
            for item in progress_report["scored_items"]:
                match_symbol = "✔️" if item.get("match") else "❌"
                text = item.get("scope", "")
                score = int(round(item.get("confidence", 0)))
                bullet = f"{match_symbol} {text} — <b>{score}%</b>"
                elements.append(Paragraph(bullet, styles["Normal"]))
                elements.append(Spacer(1, 6))
        elements.append(PageBreak())

    # --- Section 4: Safety Sheet ---
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        ext = os.path.splitext(safety_sheet_path)[1].lower()
        elements.append(Paragraph("<b>Safety Sheet</b>", styles["Heading2"]))
        elements.append(Spacer(1, 6))

        if ext == ".pdf":
            reader = PdfReader(safety_sheet_path)
            page_text = reader.pages[0].extract_text()
            elements.append(Paragraph(page_text or "First page could not be parsed.", styles["Normal"]))
        elif ext in [".jpg", ".jpeg", ".png"]:
            elements.append(Image(safety_sheet_path, width=5*inch, height=4*inch))
        else:
            elements.append(Paragraph("Unsupported safety sheet format.", styles["Normal"]))

    # --- Footer ---
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Confidential – Do Not Duplicate without written consent from BAINS Dev Comm", styles["Normal"]))

    doc.build(elements)
