from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import os


def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report, save_path,
                         weather_icon_path=None, safety_sheet_path=None):

    doc = SimpleDocTemplate(save_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Styles
    title_style = ParagraphStyle(name='Title', fontSize=18, alignment=TA_CENTER, spaceAfter=20)
    header_style = ParagraphStyle(name='Header', fontSize=14, spaceBefore=10, spaceAfter=6)
    normal = styles['Normal']

    # Logo
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=40))
        elements.append(Spacer(1, 12))

    # Title
    elements.append(Paragraph("DAILY LOG", title_style))

    # Page 1: Basic Info
    fields = ['project_name', 'location', 'date', 'supervisor']
    for field in fields:
        if field in data:
            elements.append(Paragraph(f"<b>{field.replace('_', ' ').title()}:</b> {data[field]}", normal))

    # Weather
    if 'weather' in data:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("<b>Weather:</b>", header_style))
        if weather_icon_path and os.path.exists(weather_icon_path):
            elements.append(Image(weather_icon_path, width=30, height=30))
        elements.append(Paragraph(data['weather'], normal))

    # Notes
    for section in ['crew_notes', 'work_done', 'safety_notes', 'equipment_used']:
        if section in data:
            elements.append(Paragraph(section.replace('_', ' ').title(), header_style))
            elements.append(Paragraph(data[section], normal))

    elements.append(PageBreak())

    # Page 2: Job Site Photos
    if image_paths:
        elements.append(Paragraph("Job Site Photos", title_style))
        for path in image_paths:
            try:
                img = Image(path, width=3.2 * inch, height=2.4 * inch)
                elements.append(img)
                elements.append(Spacer(1, 6))
            except Exception:
                continue
        elements.append(PageBreak())

    # Page 3: AI Scope Analysis
    if ai_analysis:
        elements.append(Paragraph("AI SCOPE ANALYSIS", title_style))
        elements.append(Paragraph(f"Completion: <b>{ai_analysis.get('completion', '0')}%</b>", normal))

        def render_list(title, items):
            if items:
                elements.append(Paragraph(title, header_style))
                for item in items:
                    elements.append(Paragraph(f"- {item}", normal))

        render_list("Matched Items", ai_analysis.get('matched', []))
        render_list("Unmatched Items", ai_analysis.get('unmatched', []))
        render_list("Out of Scope", ai_analysis.get('out_of_scope', []))
        render_list("Suggested Change Orders", ai_analysis.get('change_order_suggestions', []))

        elements.append(PageBreak())

    # Page 4: Safety Sheet (if any)
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        if safety_sheet_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            elements.append(Paragraph("Safety Sheet", title_style))
            elements.append(Image(safety_sheet_path, width=6 * inch, height=8 * inch))
        # Future: add support for PDF safety sheets if needed
        elements.append(PageBreak())

    # Build PDF
    doc.build(elements)

    # Add footer
    with open(save_path, 'rb') as f:
        reader = PdfReader(f)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            page.merge_text(40, 20, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm", size=8)
            writer.add_page(page)
        with open(save_path, 'wb') as f_out:
            writer.write(f_out)
