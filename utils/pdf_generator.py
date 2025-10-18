from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

def create_daily_log_pdf(data, output_dir):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterHeading', alignment=TA_CENTER, fontSize=16, spaceAfter=10, textColor=colors.HexColor("#003366")))
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=12, spaceAfter=6, textColor=colors.darkblue, leading=14))
    styles.add(ParagraphStyle(name='NormalText', fontSize=10, leading=12))

    pdf_path = os.path.join(output_dir, "Daily_Log.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    # Logo + Title
    logo_path = data.get("logo")
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=1.6*inch, height=1.0*inch)
        logo.hAlign = 'RIGHT'
        story.append(logo)

    story.append(Paragraph("DAILY LOG", styles['CenterHeading']))

    # Table of key header info
    header_data = [
        ["Date:", data.get("date", ""), "Prepared By:", data.get("prepared_by", "")],
        ["Project:", data.get("project_name", ""), "Job #:", data.get("job_number", "")],
        ["Client:", data.get("client_name", ""), "Location:", data.get("location", "")],
        ["GC/Sub:", data.get("gc_or_sub", ""), "Weather:", data.get("weather", "")],
    ]
    table = Table(header_data, hAlign='LEFT', colWidths=[60, 150, 60, 150])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))

    # Daily sections
    sections = [
        ("Crew Notes", data.get("crew_notes", "")),
        ("Work Performed", data.get("work_done", "")),
        ("Deliveries", data.get("deliveries", "")),
        ("Inspections", data.get("inspections", "")),
        ("Equipment Used", data.get("equipment_used", "")),
        ("Safety Notes", data.get("safety_notes", "")),
        ("Additional Notes", data.get("notes", "")),
    ]

    for title, content in sections:
        story.append(Paragraph(title, styles['SectionHeader']))
        story.append(Paragraph(content or "-", styles['NormalText']))
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # Page 2 – Photo Uploads
    photos = data.get("photos", [])
    if photos:
        story.append(Paragraph("Job Site Photos", styles['SectionHeader']))
        photo_row = []
        for i, photo_path in enumerate(photos):
            try:
                img = Image(photo_path, width=2.6*inch, height=2.0*inch)
                photo_row.append(img)
                if len(photo_row) == 2 or i == len(photos) - 1:
                    story.append(Table([photo_row], colWidths=[3*inch]*len(photo_row), hAlign='LEFT'))
                    story.append(Spacer(1, 12))
                    photo_row = []
            except Exception as e:
                print(f"Error loading image {photo_path}: {e}")

    story.append(PageBreak())

    # Page 3 – AI/AR Summary Placeholder
    story.append(Paragraph("Material Price Analysis & AR Measurement Output", styles['SectionHeader']))
    story.append(Paragraph("[AI-generated material comparison and AR analysis will appear here]", styles['NormalText']))

    # Footer – Marketing
    story.append(Spacer(1, 50))
    footer = Paragraph("<para align='center' spaceBefore='20'><font size=8>Powered by <b>Nails & Notes</b></font></para>", styles['NormalText'])
    story.append(footer)

    doc.build(story)
    return pdf_path
