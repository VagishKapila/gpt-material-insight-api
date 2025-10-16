from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from PIL import Image as PILImage
import os
import tempfile

def compress_image(original_path, max_width=800, quality=60):
    try:
        img = PILImage.open(original_path)
        img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / float(img.width)
            height = int(float(img.height) * ratio)
            img = img.resize((max_width, height), PILImage.ANTIALIAS)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(temp_file.name, format="JPEG", quality=quality)
        return temp_file.name
    except Exception as e:
        print(f"Image compression error: {e}")
        return original_path

def create_daily_log_pdf(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"DailyLog_{data.get('project_name', 'Unknown')}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(name='HeaderStyle', parent=styles['Heading2'], fontSize=14, spaceAfter=10, alignment=TA_LEFT, fontName='Helvetica-Bold')
    normal_style = styles['Normal']

    def add_section(title, content):
        elements.append(Paragraph(title, header_style))
        elements.append(Paragraph(content or "N/A", normal_style))
        elements.append(Spacer(1, 10))

    # Text sections
    add_section("Date", data.get("date"))
    add_section("Project Name", data.get("project_name"))
    add_section("Client Name", data.get("client_name"))
    add_section("Job Number", data.get("job_number"))
    add_section("Prepared By", data.get("prepared_by"))
    add_section("Location", data.get("location"))
    add_section("GC or Sub", data.get("gc_or_sub"))
    add_section("Crew Notes", data.get("crew_notes"))
    add_section("Work Done", data.get("work_done"))
    add_section("Deliveries", data.get("deliveries"))
    add_section("Inspections", data.get("inspections"))
    add_section("Equipment Used", data.get("equipment_used"))
    add_section("Safety Notes", data.get("safety_notes"))
    add_section("Weather", data.get("weather"))
    add_section("Additional Notes", data.get("notes"))

    elements.append(PageBreak())

    # Add compressed images
    if data.get("photos"):
        elements.append(Paragraph("Job Site Photos", header_style))
        for path in data["photos"]:
            try:
                compressed_path = compress_image(path)
                elements.append(RLImage(compressed_path, width=5 * inch, height=3 * inch))
                elements.append(Spacer(1, 12))
            except Exception as e:
                print(f"Photo failed: {e}")
                continue

    doc.build(elements)
    return pdf_path
