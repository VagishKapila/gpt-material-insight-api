from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfMerger
from PIL import Image as PILImage
import os

def create_daily_log_pdf(data, image_paths, logo_path=None, ai_analysis="", progress_report="", save_path="", weather_icon_path=None, safety_sheet_path=None):
    temp_path = save_path.replace(".pdf", "_temp.pdf")
    doc = SimpleDocTemplate(temp_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    header_style = ParagraphStyle(name='HeaderStyle', parent=styles['Heading2'], fontSize=16, spaceAfter=12, textColor=colors.darkblue)
    subheader_style = ParagraphStyle(name='SubheaderStyle', parent=styles['Normal'], fontSize=11, spaceAfter=8, textColor=colors.black)

    # ---- Logo ----
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=2*inch, height=1*inch))
        elements.append(Spacer(1, 12))

    # ---- Title ----
    elements.append(Paragraph("DAILY LOG", header_style))
    elements.append(Spacer(1, 6))

    # ---- Basic Info ----
    info_fields = [
        ("Project Name", data.get("project_name", "")),
        ("Location", data.get("location", "")),
        ("Date", data.get("date", "")),
        ("Weather", data.get("weather", ""))
    ]
    for label, val in info_fields:
        elements.append(Paragraph(f"<b>{label}:</b> {val}", subheader_style))

    if weather_icon_path and os.path.exists(weather_icon_path):
        elements.append(Image(weather_icon_path, width=0.5*inch, height=0.5*inch))

    elements.append(Spacer(1, 12))

    # ---- Notes ----
    notes_sections = [
        ("Crew Notes", data.get("crew_notes", "")),
        ("Work Done", data.get("work_done", "")),
        ("Safety Notes", data.get("safety_notes", ""))
    ]
    for title, text in notes_sections:
        elements.append(Paragraph(f"<b>{title}</b>", header_style))
        elements.append(Paragraph(text.replace("\n", "<br />"), subheader_style))
        elements.append(Spacer(1, 12))

    elements.append(PageBreak())

    # ---- Page 2: Job Site Images ----
    elements.append(Paragraph("Job Site Photos", header_style))
    elements.append(Spacer(1, 12))
    img_width = 3.5 * inch
    img_height = 2.5 * inch
    count = 0
    for path in image_paths:
        if os.path.exists(path):
            try:
                im = PILImage.open(path)
                if im.width > im.height:
                    im = im.rotate(270, expand=True)
                    im.save(path)
                elements.append(Image(path, width=img_width, height=img_height))
                elements.append(Spacer(1, 6))
                count += 1
                if count % 2 == 0:
                    elements.append(PageBreak())
            except Exception as e:
                print(f"[Error with image {path}]: {e}")

    if count == 0:
        elements.append(Paragraph("No job site photos uploaded.", subheader_style))

    elements.append(PageBreak())

    # ---- Page 3: AI/AR Analysis ----
    elements.append(Paragraph("AI/AR Analysis", header_style))
    elements.append(Spacer(1, 12))
    if ai_analysis:
        elements.append(Paragraph(f"<b>Image Insights:</b><br/>{ai_analysis.replace('\n', '<br/>')}", subheader_style))
    else:
        elements.append(Paragraph("No AI insights available.", subheader_style))

    elements.append(Spacer(1, 12))

    if progress_report:
        elements.append(Paragraph(f"<b>Scope Progress:</b><br/>{progress_report.replace('\n', '<br/>')}", subheader_style))
    else:
        elements.append(Paragraph("No scope progress report.", subheader_style))

    elements.append(PageBreak())

    # ---- Page 4: Safety Sheet ----
    elements.append(Paragraph("Safety Sheet Upload", header_style))
    elements.append(Spacer(1, 12))
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Image(safety_sheet_path, width=5.5 * inch, height=7 * inch))
    else:
        elements.append(Paragraph("No safety sheet uploaded.", subheader_style))

    doc.build(elements)

    # ---- Final PDF with Footer and Page Numbers ----
    merger = PdfMerger()
    merger.append(temp_path)
    merger.write(save_path)
    merger.close()
    os.remove(temp_path)
    print(f"✅ PDF created: {save_path}")
