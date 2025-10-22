from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os

def create_daily_log_pdf(data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("DAILY LOG REPORT", styles['Title']))
    elements.append(Spacer(1, 12))

    fields = [
        ("Project Name", data.get("project_name", "")),
        ("Date", data.get("date", "")),
        ("Location", data.get("location", "")),
        ("Weather", data.get("weather", "")),
        ("Crew Notes", data.get("crew_notes", "")),
        ("Work Performed", data.get("work_performed", "")),
        ("Safety Notes", data.get("safety_notes", "")),
        ("Equipment Used", data.get("equipment_used", ""))
    ]

    for label, value in fields:
        elements.append(Paragraph(f"<b>{label}:</b> {value}", styles["Normal"]))
        elements.append(Spacer(1, 8))

    # Add logo
    if data.get("logo_path") and os.path.exists(data["logo_path"]):
        elements.append(Spacer(1, 12))
        elements.append(Image(data["logo_path"], width=120, height=60))

    # Page 2 — Photos
    if data.get("images"):
        elements.append(PageBreak())
        elements.append(Paragraph("Site Photos", styles['Title']))
        elements.append(Spacer(1, 12))

        for img_path in data["images"]:
            if os.path.exists(img_path):
                elements.append(Image(img_path, width=2.5 * inch, height=2.5 * inch))
                elements.append(Spacer(1, 12))

    doc.build(elements)
