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
        try:
            logo = Image(logo_path, width=100, height=40)
            logo.hAlign = 'LEFT'
            elements.append(logo)
            elements.append(Spacer(1, 12))
        except Exception as e:
            print(f"Error loading logo: {e}")

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
            try:
                weather_icon = Image(weather_icon_path, width=30, height=30)
                weather_icon.hAlign = 'LEFT'
                elements.append(weather_icon)
            except Exception as e:
                print(f"Error loading weather icon: {e}")
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
            if os.path.exists(path) and path.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    img = Image(path, width=3.2 * inch, height=2.4 * inch)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 6))
                except Exception as e:
                    print(f"Failed to load image: {path}, error: {e}")
        elements.append(PageBreak())

    # Page 3: AI Scope Analysis
    if ai_analysis:
        elements.append(Paragraph("AI SCOPE ANALYSIS", title_style))
        try:
            completion = int(ai_analysis.get('completion', '0'))
        except (ValueError, TypeError):
            completion = 0
        progress_bar = f"[{'█' * (completion // 10)}{'░' * (10 - (completion // 10))}]"
        elements.append(Paragraph(f"Completion: <b>{completion}%</b> {progress_bar}", normal))

        def render_list(title, items):
            if items:
                elements.append(Paragraph(title, header_style))
                for item in items:
                    elements.append(Paragraph(f"- {item}", normal))

        render_list("Matched Items", ai_analysis.get('matched', []))
        render_list("Unmatched Items", ai_analysis.get('unmatched', []))
        render_list("Out of Scope", ai_analysis.get('out_of_scope', []))
        render_list("Suggested Change Orders", ai_analysis.get('change_order_suggestions', []))

        if not any(ai_analysis.get(k) for k in ['matched', 'unmatched', 'out_of_scope']):
            elements.append(Paragraph("No AI analysis could be generated from today’s log compared to the Scope of Work.", normal))

        elements.append(PageBreak())

    # Page 4: Safety Sheet (if any)
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        if safety_sheet_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            elements.append(Paragraph("Safety Sheet", title_style))
            try:
                elements.append(Image(safety_sheet_path, width=6 * inch, height=8 * inch))
            except Exception as e:
                print(f"Error loading safety sheet: {e}")
        elif safety_sheet_path.lower().endswith('.pdf'):
            print("PDF safety sheets not yet supported. Skipping render.")
        elements.append(PageBreak())

    # Build PDF
    doc.build(elements)

    # Add footer with page numbers
    with open(save_path, 'rb') as f:
        reader = PdfReader(f)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            page.merge_text(40, 20, f"Confidential – Do Not Duplicate without written consent from BAINS Dev Comm | Page {i+1}", size=8)
            writer.add_page(page)
        with open(save_path, 'wb') as f_out:
            writer.write(f_out)
