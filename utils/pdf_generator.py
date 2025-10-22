import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage


def compress_image(input_path, max_size=(400, 400)):
    img = PILImage.open(input_path)
    img.thumbnail(max_size)
    compressed_path = input_path.replace(".", "_compressed.")
    img.save(compressed_path, optimize=True, quality=40)
    return compressed_path


def create_daily_log_pdf(data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name='CenterTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=20
    )

    # Page 1 — Main Log
    elements.append(Paragraph("DAILY LOG REPORT", title_style))
    elements.append(Spacer(1, 12))

    fields = [
        ("Project Name", data.get("project_name", "")),
        ("Date", data.get("date", "")),
        ("Location", data.get("location", "")),
        ("Weather", data.get("weather", "")),
        ("Crew Notes", data.get("crew_notes", "")),
        ("Work Performed", data.get("work_performed", "")),
        ("Safety Notes", data.get("safety_notes", "")),
        ("Equipment Used", data.get("equipment_used", ""))
    ]

    for label, value in fields:
        elements.append(Paragraph(f"<b>{label}:</b> {value}", styles["Normal"]))
        elements.append(Spacer(1, 8))

    # Add logo
    if data.get("logo_path") and os.path.exists(data["logo_path"]):
        logo = Image(data["logo_path"], width=120, height=60)
        elements.append(Spacer(1, 12))
        elements.append(logo)

    # Page 2 — Photos
    images = data.get("images", [])
    if images:
        elements.append(PageBreak())
        elements.append(Paragraph("Site Photos", title_style))
        elements.append(Spacer(1, 12))

        for i, path in enumerate(images):
            try:
                compressed = compress_image(path)
                img = Image(compressed, width=2.5 * inch, height=2.5 * inch)
                elements.append(img)
                elements.append(Spacer(1, 6))
            except Exception as e:
                elements.append(Paragraph(f"Error loading image {path}: {str(e)}", styles["Normal"]))
                elements.append(Spacer(1, 6))

    doc.build(elements)
