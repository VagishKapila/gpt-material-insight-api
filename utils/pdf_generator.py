import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch

def create_daily_log_pdf(form_data, photo_paths=None, logo_path=None, include_page_2=True):
    output_dir = "static/generated"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{form_data.get('project_name','Project')}_Report_{datetime.now().date()}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=18, leading=22, spaceAfter=10))
    styles.add(ParagraphStyle(name='SectionHeader', fontSize=14, leading=18, spaceAfter=6, textColor=colors.HexColor('#003262')))
    styles.add(ParagraphStyle(name='NormalLeft', fontSize=11, leading=14, alignment=TA_LEFT))

    # HEADER
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=40))
    elements.append(Paragraph("DAILY LOG", styles['CenterTitle']))
    elements.append(Spacer(1, 12))

    # Project info
    fields = [
        ("Date", form_data.get("date")),
        ("Project Name", form_data.get("project_name")),
        ("Client", form_data.get("client_name")),
        ("Location", form_data.get("address")),
        ("Weather", form_data.get("weather")),
        ("Crew Notes", form_data.get("crew_notes")),
        ("Work Done", form_data.get("work_done")),
        ("Safety Notes", form_data.get("safety_notes")),
        ("Equipment Used", form_data.get("equipment_used")),
        ("Material Summary", form_data.get("material_summary")),
        ("Hours Worked", form_data.get("hours_worked"))
    ]

    for label, value in fields:
        if not value:
            continue
        elements.append(Paragraph(f"<b>{label}:</b> {value}", styles['NormalLeft']))
        elements.append(Spacer(1, 8))

    # Page 2 – Photos
    if include_page_2 and photo_paths:
        elements.append(PageBreak())
        elements.append(Paragraph("Jobsite Photos", styles['SectionHeader']))

        image_table = []
        row = []
        for idx, path in enumerate(photo_paths):
            if os.path.exists(path):
                img = Image(path, width=2.5 * inch, height=2 * inch)
                row.append(img)
                if (idx + 1) % 2 == 0:
                    image_table.append(row)
                    row = []
        if row:
            image_table.append(row)
        if image_table:
            t = Table(image_table, hAlign='LEFT', spaceBefore=10)
            t.setStyle(TableStyle([('BOTTOMPADDING', (0, 0), (-1, -1), 12)]))
            elements.append(t)

    doc.build(elements)
    return filename
