from reportlab.lib.pagesizes import letter
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
                                  Table, TableStyle, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib import colors
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
            img = img.resize((max_width, height), PILImage.Resampling.LANCZOS)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(temp_file.name, format="JPEG", quality=quality)
        return temp_file.name
    except Exception as e:
        print(f"[Image Compression Error] {e}")
        return original_path


def create_daily_log_pdf(data, output_dir, logo_path=None):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"DailyLog_{data.get('project_name', 'Unknown')}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(name='HeaderStyle', parent=styles['Heading2'], fontSize=13,
                                  textColor=colors.darkblue, spaceAfter=8, alignment=TA_LEFT,
                                  fontName='Helvetica-Bold')
    normal_style = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontSize=10)

    def add_section(title, content):
        elements.append(Paragraph(title, header_style))
        elements.append(Paragraph(content or "N/A", normal_style))
        elements.append(Spacer(1, 6))

    # Title + Logo Row
    table_data = [[Paragraph("<b>DAILY LOG</b>", styles['Title'])]]
    if logo_path:
        try:
            compressed_logo = compress_image(logo_path, max_width=150)
            table_data[0].append(RLImage(compressed_logo, width=1.2*inch, height=0.6*inch))
        except Exception as e:
            print(f"[Logo Error] {e}")
            table_data[0].append("")

    logo_table = Table(table_data, colWidths=[5.5*inch, 1.5*inch])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    elements.append(logo_table)
    elements.append(Spacer(1, 12))

    # Section Blocks
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

    # Photos Section
    if data.get("photos"):
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Job Site Photos", header_style))
        for path in data["photos"]:
            try:
                compressed_path = compress_image(path)
                elements.append(RLImage(compressed_path, width=5*inch, height=3*inch))
                elements.append(Spacer(1, 10))
            except Exception as e:
                print(f"[Photo Skipped] {e}")
                continue

    elements.append(PageBreak())

    # Page 2 - Material Comparison Table
    elements.append(Paragraph("Material Price Comparison", header_style))
    comparison_data = [["Material", "Supplier", "Price", "Notes"]]
    for row in data.get("material_comparison", []):
        comparison_data.append([row.get("material", ""), row.get("supplier", ""),
                                row.get("price", ""), row.get("notes", "")])

    table = Table(comparison_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(table)

    # Footer Branding
    elements.append(Spacer(1, 30))
    footer = Paragraph("<font size=8 color='grey'><i>Powered by Nails & Notes</i></font>", normal_style)
    elements.append(footer)

    doc.build(elements)
    return pdf_path
