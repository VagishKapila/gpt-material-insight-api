import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

# ==========================
# Utility: Safe image compression
# ==========================
def compress_image(input_path, max_size=(1200, 1200)):
    try:
        img = PILImage.open(input_path)
        img.thumbnail(max_size)
        temp_path = input_path.replace(".", "_compressed.")
        img.save(temp_path, optimize=True, quality=70)
        return temp_path
    except Exception:
        return input_path

# ==========================
# Core PDF builder
# ==========================
def create_daily_log_pdf(form_data, photo_paths, logo_path=None, include_page_2=False):
    os.makedirs("static/generated", exist_ok=True)

    project_name = form_data.get("project_name", "Project")
    address = form_data.get("address", "")
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{project_name.replace(' ', '_')}_Report_{date_str}.pdf"
    pdf_path = os.path.join("static/generated", filename)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = []

    # Header section
    header_style = ParagraphStyle("HeaderTitle", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#002060"), spaceAfter=10)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#1F4E79"), spaceBefore=12)
    normal = ParagraphStyle("Normal", parent=styles["BodyText"], fontSize=10, leading=14)

    # ==========================
    # PAGE 1
    # ==========================
    if logo_path and os.path.exists(logo_path):
        logo_temp = compress_image(logo_path, (150, 150))
        elements.append(Image(logo_temp, width=1.5 * inch, height=1.5 * inch))
    else:
        elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph("DAILY LOG REPORT", header_style))
    elements.append(Spacer(1, 6))

    # Info Table
    info_data = [
        ["Date", form_data.get("date", date_str)],
        ["Project Name", project_name],
        ["Client", form_data.get("client_name", "")],
        ["Address", address],
        ["General Contractor", form_data.get("general_contractor", "")],
        ["Weather", form_data.get("weather", "N/A")],
        ["Hours Worked", form_data.get("hours_worked", "")]
    ]
    info_table = Table(info_data, colWidths=[1.8 * inch, 4.5 * inch])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E1F2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 12))

    # Main content sections
    def add_section(title, text):
        elements.append(Paragraph(title, section_style))
        elements.append(Paragraph(text or "—", normal))
        elements.append(Spacer(1, 8))

    add_section("Crew Notes", form_data.get("crew_notes", ""))
    add_section("Work Done", form_data.get("work_done", ""))
    add_section("Equipment Used", form_data.get("equipment_used", ""))
    add_section("Safety Notes", form_data.get("safety_notes", ""))
    add_section("Material Summary", form_data.get("material_summary", ""))

    # ==========================
    # PHOTO GRID
    # ==========================
    if photo_paths:
        elements.append(Paragraph("Job Site Photos", section_style))
        img_table_data, row = [], []
        for i, path in enumerate(photo_paths):
            try:
                img_temp = compress_image(path, (400, 400))
                row.append(Image(img_temp, width=2.4 * inch, height=2.4 * inch))
                if (i + 1) % 2 == 0:
                    img_table_data.append(row)
                    row = []
            except Exception:
                continue
        if row:
            img_table_data.append(row)
        elements.append(Table(img_table_data, hAlign="LEFT"))
        elements.append(Spacer(1, 12))

    # Footer
    footer_text = Paragraph("<para align='right'><font size=8 color='#999999'>Powered by Nails & Notes</font></para>", styles["Normal"])
    elements.append(footer_text)

    # ==========================
    # PAGE 2 - AI/AR ANALYSIS
    # ==========================
    if include_page_2:
        elements.append(PageBreak())
        elements.append(Paragraph("AI / AR ANALYSIS & COMPARATIVE INSIGHTS", header_style))
        elements.append(Spacer(1, 10))

        ai_text = """
        This section is auto‑generated by AI and AR systems (in development).  
        Future versions will include:
        <ul>
          <li>⚙️ Material detection & cost comparison</li>
          <li>📏 AR‑based site measurement validation</li>
          <li>🧠 Image captioning and context analysis</li>
          <li>💲 Supplier price comparison charts</li>
        </ul>
        """
        elements.append(Paragraph(ai_text, normal))
        elements.append(Spacer(1, 12))

        table_data = [
            ["Material", "Supplier", "Unit Price ($)", "Notes"],
            ["Concrete", "Lowe's", "7.50", "Standard Mix 80lb bag"],
            ["Steel Rebar", "Home Depot", "1.20", "Per foot"],
            ["PVC Pipe", "Ferguson", "3.10", "Schedule 40, 2‑inch"]
        ]
        ai_table = Table(table_data, colWidths=[1.5 * inch] * 4)
        ai_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#CFE2F3")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))
        elements.append(ai_table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph(
            "🔍 This data will later merge with AI outputs from your uploaded site images to detect materials, "
            "estimate pricing, and benchmark vendor options automatically.", normal))

        elements.append(Spacer(1, 24))
        footer_text2 = Paragraph("<para align='right'><font size=8 color='#999999'>Powered by Nails & Notes</font></para>", styles["Normal"])
        elements.append(footer_text2)

    # Build PDF
    doc.build(elements)
    return filename
