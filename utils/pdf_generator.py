
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os

def create_daily_log_pdf(data, photo_paths=None, logo_path=None, include_page_2=False):
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_filename = f"DailyLog_{now}.pdf"
    output_path = os.path.join("static/generated", output_filename)

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=10)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], spaceAfter=6)
    normal_style = styles['Normal']

    # Logo if available
    if logo_path and os.path.exists(logo_path):
        img = Image(logo_path, width=150, height=60)
        story.append(img)
        story.append(Spacer(1, 12))

    # Title
    story.append(Paragraph("DAILY LOG REPORT", title_style))
    story.append(Spacer(1, 12))

    # Main fields
    fields = [
        ("Date", data.get("date", "")),
        ("Project Name", data.get("project_name", "")),
        ("Client", data.get("client_name", "")),
        ("Location", data.get("location", "")),
        ("Weather", data.get("weather", "")),
        ("Crew Notes", data.get("crew_notes", "")),
        ("Work Performed", data.get("work_performed", "")),
        ("Safety Notes", data.get("safety_notes", "")),
        ("Additional Notes", data.get("additional_notes", "")),
    ]

    for label, value in fields:
        story.append(Paragraph(f"<b>{label}:</b> {value}", normal_style))
        story.append(Spacer(1, 6))

    # Page 2 placeholder (if requested)
    if include_page_2:
        story.append(PageBreak())
        story.append(Paragraph("Page 2 – AI/AR Material Analysis", section_style))
        story.append(Paragraph("Coming soon: material comparison, supplier options, and AR-based insights.", normal_style))

    # Photos
    if photo_paths:
        story.append(PageBreak())
        story.append(Paragraph("Job Site Photos", section_style))
        for img_path in photo_paths:
            if os.path.exists(img_path):
                try:
                    img = Image(img_path, width=400, height=300)
                    story.append(img)
                    story.append(Spacer(1, 12))
                except Exception as e:
                    story.append(Paragraph(f"Could not load image {img_path}: {e}", normal_style))

    # Build PDF
    doc.build(story)

    return output_filename
