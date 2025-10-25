from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os

# === UTILS ===
def create_table(data, col_widths):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    return table

def add_footer(canvas_obj, doc):
    page_num = canvas_obj.getPageNumber()
    text = f"Confidential – Do Not Duplicate without written consent from BAINS Dev Comm   |   Page {page_num}"
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 7)
    canvas_obj.setFillColor(colors.grey)
    canvas_obj.drawString(40, 20, text)
    canvas_obj.restoreState()

# === MAIN FUNCTION ===
def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report, save_path, weather_icon_path=None, safety_sheet_path=None, scope_result=None):
    doc = SimpleDocTemplate(save_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Heading', fontSize=14, leading=16, spaceAfter=12, spaceBefore=12, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SubHeading', fontSize=11, leading=14, spaceAfter=8, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='NormalBold', fontSize=10, fontName='Helvetica-Bold'))

    elements = []

    # === PAGE 1: HEADER ===
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=40))
    elements.append(Paragraph("DAILY LOG REPORT", styles['Heading']))

    meta_data = [
        ["Project Name:", data.get("project_name", "")],
        ["Location:", data.get("location", "")],
        ["Date:", data.get("date", "")],
        ["Supervisor:", data.get("supervisor", "")],
        ["Client Name:", data.get("client_name", "")],
        ["Weather:", data.get("weather", "")]
    ]
    elements.append(create_table(meta_data, [120, 350]))
    elements.append(Spacer(1, 16))

    # === CREW / WORK DONE ===
    elements.append(Paragraph("Crew On Site:", styles['SubHeading']))
    elements.append(Paragraph(data.get("crew", "N/A"), styles['Normal']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Work Performed:", styles['SubHeading']))
    elements.append(Paragraph(data.get("work_done", "N/A"), styles['Normal']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Safety Notes:", styles['SubHeading']))
    elements.append(Paragraph(data.get("safety_notes", "N/A"), styles['Normal']))
    elements.append(PageBreak())

    # === PAGE 2: JOB SITE PHOTOS ===
    elements.append(Paragraph("Job Site Photos", styles['Heading']))
    if not image_paths:
        elements.append(Paragraph("No photos uploaded.", styles['Normal']))
    else:
        for i, img_path in enumerate(image_paths):
            if os.path.exists(img_path):
                elements.append(Image(img_path, width=250, height=150))
                elements.append(Spacer(1, 8))
                if (i + 1) % 2 == 0:
                    elements.append(PageBreak())
    elements.append(PageBreak())

    # === PAGE 3: AI SCOPE COMPARISON ===
    if ai_analysis and scope_result:
        elements.append(Paragraph("AI Scope Comparison", styles['Heading']))
        if scope_result.get("completion"):
            percent = scope_result["completion"]
            elements.append(Paragraph(f"Estimated Completion: {percent}%", styles['Normal']))
        if scope_result.get("summary"):
            elements.append(Paragraph(scope_result["summary"], styles['Normal']))
        elements.append(PageBreak())

    # === PAGE 4: SAFETY SHEET ===
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("Safety Documentation", styles['Heading']))
        elements.append(Image(safety_sheet_path, width=400, height=550))

    doc.build(elements, onLaterPages=add_footer, onFirstPage=add_footer)
