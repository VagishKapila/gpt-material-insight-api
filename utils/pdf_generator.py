from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image as PILImage, ExifTags
import os
import io

def fix_image_orientation(path):
    try:
        image = PILImage.open(path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation, None)
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
        return image
    except Exception:
        return PILImage.open(path)  # fallback

def create_temp_image(image: PILImage.Image) -> str:
    temp_path = f"temp_{os.getpid()}.jpg"
    image.save(temp_path, format="JPEG")
    return temp_path

def add_footer(canvas, doc):
    footer_text = "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm"
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, 0.5 * inch, footer_text)
    canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.restoreState()

def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report, save_path, weather_icon_path, safety_sheet_path):
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Page 1 – Daily Log
    elements.append(Paragraph("DAILY LOG", styles['Title']))
    if logo_path:
        elements.append(Image(logo_path, width=100, height=50))
    elements.append(Spacer(1, 0.2 * inch))
    for key in ['project_name', 'client_name', 'location', 'date', 'weather']:
        if key in data:
            elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {data[key]}", styles['Normal']))
    if weather_icon_path:
        elements.append(Image(weather_icon_path, width=40, height=40))
    elements.append(Spacer(1, 0.2 * inch))
    for section in ['crew_notes', 'work_done', 'safety_notes']:
        if section in data:
            elements.append(Paragraph(f"<b>{section.replace('_', ' ').title()}:</b>", styles['Heading3']))
            elements.append(Paragraph(data[section], styles['Normal']))
            elements.append(Spacer(1, 0.15 * inch))
    elements.append(PageBreak())

    # Page 2 – Photos
    elements.append(Paragraph("JOB SITE PHOTOS", styles['Title']))
    for i, img_path in enumerate(image_paths):
        pil_image = fix_image_orientation(img_path)
        temp_img = create_temp_image(pil_image)
        elements.append(Image(temp_img, width=5*inch, height=3*inch))
        elements.append(Spacer(1, 0.1 * inch))
    elements.append(PageBreak())

    # Page 3 – AI / AR Analysis
    if ai_analysis or progress_report:
        elements.append(Paragraph("AI / AR COMPARISON", styles['Title']))
        if ai_analysis:
            elements.append(Paragraph("<b>AI Analysis:</b>", styles['Heading3']))
            elements.append(Paragraph(ai_analysis, styles['Normal']))
        if progress_report:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("<b>Scope Progress:</b>", styles['Heading3']))
            elements.append(Paragraph(progress_report, styles['Normal']))
        elements.append(PageBreak())

    # Page 4 – Safety Sheet
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("DAILY SAFETY SHEET", styles['Title']))
        if safety_sheet_path.lower().endswith((".jpg", ".jpeg", ".png")):
            pil_image = fix_image_orientation(safety_sheet_path)
            temp_img = create_temp_image(pil_image)
            elements.append(Image(temp_img, width=6.5*inch, height=9*inch))
        elif safety_sheet_path.lower().endswith(".pdf"):
            try:
                with open(safety_sheet_path, 'rb') as f:
                    reader = PdfReader(f)
                    writer = PdfWriter()
                    for page in reader.pages:
                        writer.add_page(page)
                    with open("temp_safety.pdf", "wb") as out_f:
                        writer.write(out_f)
                elements.append(Paragraph("See attached PDF", styles['Normal']))
            except Exception as e:
                elements.append(Paragraph(f"Failed to include PDF: {str(e)}", styles['Normal']))
        elements.append(PageBreak())

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    # Clean up temporary files
    for f in os.listdir():
        if f.startswith("temp_") and f.endswith(".jpg"):
            os.remove(f)
