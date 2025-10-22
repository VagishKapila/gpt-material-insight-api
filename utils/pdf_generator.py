from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import os

def create_daily_log_pdf(output_path, data, photo_paths=None, logo_path=None):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []

    def add_header(title):
        Story.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
        Story.append(Spacer(1, 6))

    # Add logo if provided
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=100, height=50)
            Story.append(logo)
            Story.append(Spacer(1, 12))
        except Exception as e:
            print("Logo load error:", e)

    Story.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    Story.append(Spacer(1, 12))

    # Add project and weather details
    for key in ["project_name", "project_address", "client", "date", "weather"]:
        if key in data:
            Story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {data[key]}", styles["Normal"]))
            Story.append(Spacer(1, 6))

    Story.append(Spacer(1, 12))

    # Add main sections
    sections = {
        "crew_notes": "Crew Notes",
        "work_done": "Work Completed",
        "equipment_used": "Equipment Used",
        "safety_notes": "Safety Notes",
        "additional_notes": "Additional Notes"
    }

    for field, title in sections.items():
        if field in data and data[field].strip():
            add_header(title)
            Story.append(Paragraph(data[field], styles["Normal"]))
            Story.append(Spacer(1, 12))

    # Add photos if provided
    if photo_paths:
        Story.append(PageBreak())
        Story.append(Paragraph("<b>Job Site Photos</b>", styles["Heading2"]))
        Story.append(Spacer(1, 12))
        for path in photo_paths:
            if os.path.exists(path):
                try:
                    img = Image(path, width=400, height=300)
                    Story.append(img)
                    Story.append(Spacer(1, 12))
                except Exception as e:
                    print("Image load error:", e)

    doc.build(Story)
