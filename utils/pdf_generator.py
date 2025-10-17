from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
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
            img = img.resize((max_width, height), PILImage.Resampling.LANCZOS)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(temp_file.name, format="JPEG", quality=quality)
        return temp_file.name
    except Exception as e:
        print(f"[Image Compression Error] {e}")
        return original_path

def create_daily_log_pdf(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"DailyLog_{data.get('project_name', 'Unknown')}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    header_style = ParagraphStyle('HeaderStyle', fontSize=14, spaceAfter=10, textColor=colors.HexColor("#1a73e8"), fontName='Helvetica-Bold')
    subhead_style = ParagraphStyle('SubHeadStyle', fontSize=12, spaceAfter=6, textColor=colors.black)

    # Header section: logo + title
    logo_path = data.get("logo_path")
    if logo_path:
        try:
            compressed_logo = compress_image(logo_path, max_width=150)
            elements.append(RLImage(compressed_logo, width=1.8*inch, height=0.8*inch))
        except Exception as e:
            print(f"[Logo Error] {e}")
    elements.append(Paragraph("DAILY LOG", header_style))
    elements.append(Spacer(1, 10))

    # Job Info Table (side-by-side)
    def make_info_row(label, value):
        return [Paragraph(f"<b>{label}</b>", subhead_style), Paragraph(value or "N/A", normal)]

    info_table_data = [
        make_info_row("Date", data.get("date")),
        make_info_row("Project Name", data.get("project_name")),
        make_info_row("Client Name", data.get("client_name")),
        make_info_row("Job Number", data.get("job_number")),
        make_info_row("Prepared By", data.get("prepared_by")),
        make_info_row("Location", data.get("location")),
        make_info_row("GC or Sub", data.get("gc_or_sub")),
    ]

    table = Table(info_table_data, colWidths=[1.8*inch, 4.7*inch])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Sectioned Notes
    def add_section(title, content):
        elements.append(Paragraph(title, header_style))
        elements.append(Paragraph(content or "N/A", normal))
        elements.append(Spacer(1, 10))

    add_section("Crew Notes", data.get("crew_notes"))
    add_section("Work Done", data.get("work_done"))
    add_section("Deliveries", data.get("deliveries"))
    add_section("Inspections", data.get("inspections"))
    add_section("Equipment Used", data.get("equipment_used"))
    add_section("Safety Notes", data.get("safety_notes"))
    add_section("Additional Notes", data.get("notes"))

    # Weather with icon if available
    elements.append(Paragraph("Weather", header_style))
    weather_text = data.get("weather") or "N/A"
    icon_path = data.get("weather_icon_path")
    if icon_path:
        try:
            compressed_icon = compress_image(icon_path, max_width=50)
            weather_row = Table([
                [Paragraph(weather_text, normal), RLImage(compressed_icon, width=0.5*inch, height=0.5*inch)]
            ])
            elements.append(weather_row)
        except Exception as e:
            print(f"[Weather Icon Error] {e}")
            elements.append(Paragraph(weather_text, normal))
    else:
        elements.append(Paragraph(weather_text, normal))
    elements.append(Spacer(1, 12))

    # Job Site Photos
    if data.get("photos"):
        elements.append(PageBreak())
        elements.append(Paragraph("Job Site Photos", header_style))
        for idx, path in enumerate(data["photos"], start=1):
            try:
                compressed = compress_image(path)
                elements.append(RLImage(compressed, width=5 * inch, height=3 * inch))
                elements.append(Spacer(1, 10))
            except Exception as e:
                print(f"[Photo Skipped - {idx}] {e}")
                continue

    # Optional Page 2 — Analysis (for now, placeholder)
    if data.get("include_page_2"):
        elements.append(PageBreak())
        elements.append(Paragraph("Page 2: Comparative Material Pricing Analysis", header_style))
        analysis_text = """
        <ul>
            <li><b>Material:</b> Sheetrock</li>
            <li><b>Cheapest Option:</b> Lowe’s - $8</li>
            <li><b>Alternative Supplier:</b> Home Depot - $8.75</li>
            <li><b>Bulk Discount:</b> Yes, above 50 units</li>
        </ul>
        """
        elements.append(Paragraph(analysis_text, normal))
        elements.append(Spacer(1, 20))

    # Footer / Signature
    footer = Paragraph("<para align=center><font size=10 color='#888888'>Powered by <b>Nails & Notes</b></font></para>", styles["Normal"])
    elements.append(Spacer(1, 40))
    elements.append(footer)

    doc.build(elements)
    return pdf_path
