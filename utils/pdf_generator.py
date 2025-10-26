from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
import os

def create_daily_log_pdf(
    data,
    image_paths,
    logo_path,
    ai_analysis,
    progress_report,
    save_path,
    weather_icon_path=None,
    safety_sheet_path=None
):
    doc = SimpleDocTemplate(save_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(name="Title", fontSize=18, alignment=TA_CENTER, spaceAfter=20)
    header_style = ParagraphStyle(name="Header", fontSize=14, spaceBefore=10, spaceAfter=6)
    normal = styles["Normal"]

    # ---- Logo ----
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=100, height=40)
            logo.hAlign = "LEFT"
            elements.append(logo)
            elements.append(Spacer(1, 12))
        except Exception as e:
            print(f"⚠️ Error loading logo: {e}")

    # ---- Title ----
    elements.append(Paragraph("DAILY LOG", title_style))

    # ---- Page 1: Basic Info ----
    for field in ["project_name", "client_name", "location", "date", "supervisor"]:
        if field in data and data[field].strip():
            label = field.replace("_", " ").title()
            elements.append(Paragraph(f"<b>{label}:</b> {data[field]}", normal))

    # ---- Weather ----
    if "weather" in data and data["weather"].strip():
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("<b>Weather:</b>", header_style))
        if weather_icon_path and os.path.exists(weather_icon_path):
            try:
                weather_icon = Image(weather_icon_path, width=30, height=30)
                weather_icon.hAlign = "LEFT"
                elements.append(weather_icon)
            except Exception as e:
                print(f"⚠️ Error loading weather icon: {e}")
        elements.append(Paragraph(data["weather"], normal))

    # ---- Notes Sections ----
    for section in ["crew_notes", "work_done", "safety_notes", "equipment_used"]:
        if section in data and data[section].strip():
            elements.append(Paragraph(section.replace("_", " ").title(), header_style))
            elements.append(Paragraph(data[section], normal))

    elements.append(PageBreak())

    # ---- Page 2: Job Site Photos ----
    if image_paths:
        elements.append(Paragraph("Job Site Photos", title_style))
        for path in image_paths:
            if os.path.exists(path) and path.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    img = Image(path, width=3.2 * inch, height=2.4 * inch)
                    img.hAlign = "CENTER"
                    elements.append(img)
                    elements.append(Spacer(1, 6))
                except Exception as e:
                    print(f"⚠️ Failed to load image {path}: {e}")
        elements.append(PageBreak())

    # ---- Page 3: AI Scope Analysis ----
    if ai_analysis:
        elements.append(Paragraph("AI / SCOPE ANALYSIS", title_style))

        try:
            completion = int(ai_analysis.get("completion", ai_analysis.get("progress", 0)))
        except (ValueError, TypeError):
            completion = 0

        # Draw progress bar
        progress_bar = f"[{'█' * (completion // 10)}{'░' * (10 - (completion // 10))}]"
        elements.append(Paragraph(f"Completion: <b>{completion}%</b> {progress_bar}", normal))
        elements.append(Spacer(1, 6))

        def render_confidence_table(title, item_list):
            if not item_list:
                return
            elements.append(Paragraph(title, header_style))
            data = [["Item", "Confidence"]]
            for item in item_list:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    conf = round(item.get("confidence", 0) * 100)
                    data.append([text, f"{conf}%"])
                else:
                    data.append([str(item), "–"])
            t = Table(data, colWidths=[400, 100])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))

        render_confidence_table("✔️ Matched Items", ai_analysis.get("matched", []))
        render_confidence_table("⏳ Unmatched Items", ai_analysis.get("unmatched", []))
        render_confidence_table("❌ Out of Scope", ai_analysis.get("out_of_scope", []))
        render_confidence_table("🔁 Suggested Change Orders", ai_analysis.get("change_order_suggestions", []))

        elements.append(PageBreak())

    # ---- Page 4: Safety Sheet ----
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("Safety Sheet", title_style))
        if safety_sheet_path.lower().endswith((".png", ".jpg", ".jpeg")):
            try:
                elements.append(Image(safety_sheet_path, width=6 * inch, height=8 * inch))
            except Exception as e:
                print(f"⚠️ Error loading safety sheet: {e}")
        elif safety_sheet_path.lower().endswith(".pdf"):
            print("⚠️ PDF safety sheets not yet rendered (planned for later).")
        elements.append(PageBreak())

    # ---- Build PDF ----
    doc.build(elements)

    # ---- Add footer + page numbers ----
    try:
        with open(save_path, "rb") as f:
            reader = PdfReader(f)
            writer = PdfWriter()
            for i, page in enumerate(reader.pages):
                footer_text = (
                    "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm"
                    f" | Page {i+1}"
                )
                page.merge_text(40, 20, footer_text, size=8)
                writer.add_page(page)
            with open(save_path, "wb") as f_out:
                writer.write(f_out)
    except Exception as e:
        print(f"⚠️ Error adding footer: {e}")
