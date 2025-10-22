from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from datetime import datetime

def create_daily_log_pdf(data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=18, leading=22, spaceAfter=10))
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, leading=18, spaceAfter=6, textColor=colors.HexColor('#003262')))
    styles.add(ParagraphStyle(name='NormalLeft', fontSize=11, leading=14, alignment=TA_LEFT))

    # HEADER: Logo + Title
    logo_path = data.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=40))
    elements.append(Paragraph("DAILY LOG", styles['CenterTitle']))
    elements.append(Spacer(1, 12))

    # Project Info
    project_info = (
        f"<b>Project:</b> {data.get('project_name', '')}<br/>"
        f"<b>Date:</b> {data.get('date', datetime.today().strftime('%Y-%m-%d'))}<br/>"
        f"<b>Location:</b> {data.get('location', '')}<br/>"
        f"<b>Client:</b> {data.get('client_name', '')}<br/>"
    )
    elements.append(Paragraph(project_info, styles['NormalLeft']))
    elements.append(Spacer(1, 12))

    # Weather
    elements.append(Paragraph("Weather", styles['SectionHeader']))
    elements.append(Paragraph(data.get("weather", "N/A"), styles['NormalLeft']))
    elements.append(Spacer(1, 12))

    # Work Summary
    elements.append(Paragraph("Work Performed", styles['SectionHeader']))
    elements.append(Paragraph(data.get("work_done", "N/A"), styles['NormalLeft']))
    elements.append(Spacer(1, 12))

    # Crew
    elements.append(Paragraph("Crew Notes", styles['SectionHeader']))
    elements.append(Paragraph(data.get("crew_notes", "N/A"), styles['NormalLeft']))
    elements.append(Spacer(1, 12))

    # Safety Notes
    elements.append(Paragraph("Safety Notes", styles['SectionHeader']))
    elements.append(Paragraph(data.get("safety_notes", "N/A"), styles['NormalLeft']))
    elements.append(Spacer(1, 12))

    # Equipment
    elements.append(Paragraph("Equipment Used", styles['SectionHeader']))
    elements.append(Paragraph(data.get("equipment_used", "N/A"), styles['NormalLeft']))
    elements.append(Spacer(1, 12))

    # Additional Notes
    elements.append(Paragraph("Additional Notes", styles['SectionHeader']))
    elements.append(Paragraph(data.get("additional_notes", "N/A"), styles['NormalLeft']))
    elements.append(PageBreak())

    # Jobsite Photos Page
    images = data.get("image_paths", [])
    if images:
        elements.append(Paragraph("Jobsite Photos", styles['SectionHeader']))
        image_table = []
        row = []
        for idx, img_path in enumerate(images):
            if os.path.exists(img_path):
                img = Image(img_path, width=2.5 * inch, height=2 * inch)
                row.append(img)
                if (idx + 1) % 2 == 0:
                    image_table.append(row)
                    row = []
        if row:
            image_table.append(row)
        t = Table(image_table, hAlign='LEFT', spaceBefore=10)
        t.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 12)]))
        elements.append(t)

    doc.build(elements)
