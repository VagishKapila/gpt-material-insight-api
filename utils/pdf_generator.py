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
        if exif:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
        return image
    except Exception as e:
        print(f"EXIF fix failed for {path}: {e}")
        return PILImage.open(path)

def create_temp_image(image: PILImage.Image) -> str:
    temp_path = f"temp_{os.getpid()}_{uuid.uuid4().hex[:6]}.jpg"
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
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []

    # Page 1 – Daily Log
    elements.append(Paragraph("DAILY LOG", styles['Title']))
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=50))
    elements.append(Spacer(1, 0.2 * inch))
    for key in ['project_name', 'client_name', 'location', 'date', 'weather']:
        if key in data:
            elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {data[key]}", styles['Normal']))
    if weather_icon_path and os.path.exists(weather_icon_path):
        elements.append(Image(weather_icon_path, width=40, height=40))
    elements.append(Spacer(1, 0.2 * inch))
    for section in ['crew_notes', 'work_done', 'safety_notes']:
        if section in data:
            elements.append(Paragraph(f"<b>{section.replace('_', ' ').title()}:</b>", styles['Heading3']))
            elements.append(Paragraph(data[section], styles['Normal']))
            elements.append(Spacer(1, 0.15 * inch))
    elements.append(PageBreak())

    # Page 2 – Job Site Photos
    elements.append(Paragraph("JOB SITE PHOTOS", styles['Title']))
    for path in image_paths:
        try:
            pil_image = fix_image_orientation(path)
            temp_img = create_temp_image(pil_image)
            elements.append(Image(temp_img, width=5.5 * inch, height=3.5 * inch))
            elements.append(Spacer(1, 0.1 * inch))
        except Exception as e:
            elements.append(Paragraph(f"Could not load image: {path}", styles["Normal"]))
            elements.append(Spacer(1, 0.1 * inch))
    elements.append(PageBreak())

  # Page 3 – AI / AR
if ai_analysis or progress_report:
    elements.append(Paragraph("AI / AR COMPARISON", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    # Safely convert boolean to string for AI Analysis
    if isinstance(ai_analysis, bool):
        ai_text = "Enabled" if ai_analysis else "Disabled"
    else:
        ai_text = str(ai_analysis)

    elements.append(Paragraph("<b>AI Analysis:</b>", styles['Heading3']))
    elements.append(Paragraph(ai_text, styles['Normal']))

    if progress_report:
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("<b>Scope Progress:</b>", styles['Heading3']))
        elements.append(Paragraph(progress_report, styles['Normal']))

    elements.append(PageBreak())

    # Page 4 – Safety Sheet
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("DAILY SAFETY SHEET", styles['Title']))
        ext = os.path.splitext(safety_sheet_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png"]:
            try:
                pil_image = fix_image_orientation(safety_sheet_path)
                temp_img = create_temp_image(pil_image)
                elements.append(Image(temp_img, width=6.5 * inch, height=9 * inch))
            except Exception as e:
                elements.append(Paragraph(f"Error loading image: {str(e)}", styles["Normal"]))
        elif ext == ".pdf":
            elements.append(Paragraph("Safety sheet PDF attached separately.", styles["Normal"]))
        elif ext in [".doc", ".docx", ".xls", ".xlsx"]:
            elements.append(Paragraph("Uploaded safety sheet file (Word/Excel) included in records.", styles["Normal"]))
        else:
            elements.append(Paragraph("Unsupported safety file type.", styles["Normal"]))
        elements.append(PageBreak())

    # Build
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    # Cleanup temp files
    for f in os.listdir():
        if f.startswith("temp_") and f.endswith(".jpg"):
            try:
                os.remove(f)
            except:
                pass
