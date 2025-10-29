import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage, ExifTags

def fix_orientation_and_compress(image_path):
    try:
        img = PILImage.open(image_path)
        img = img.convert("RGB")

        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
        except Exception:
            pass

        img.thumbnail((800, 800))
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        return temp_path
    except Exception:
        return image_path

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
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title = styles["Title"]
    header_style = styles["Heading2"]

    # Logo
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=50))
        elements.append(Spacer(1, 12))

    # Header
    elements.append(Paragraph("<b>DAILY LOG</b>", title))
    elements.append(Spacer(1, 12))
    for key in ["project_name", "client_name", "location", "date", "weather"]:
        if key in data:
            label = key.replace("_", " ").title()
            elements.append(Paragraph(f"<b>{label}:</b> {data[key]}", normal))
    elements.append(Spacer(1, 12))

    # Work, Crew, Safety Notes
    for section in ["work_done", "crew_notes", "safety_notes"]:
        if section in data:
            elements.append(Paragraph(f"<b>{section.replace('_', ' ').title()}</b>", header_style))
            items = data[section].split("\n")
            for item in items:
                elements.append(Paragraph(f"- {item.strip()}", normal))
            elements.append(Spacer(1, 12))

    # Jobsite Photos
    if image_paths:
        elements.append(PageBreak())
        elements.append(Paragraph("Jobsite Photos", header_style))
        for img_path in image_paths:
            fixed_path = fix_orientation_and_compress(img_path)
            elements.append(Image(fixed_path, width=4*inch, height=3*inch))
            elements.append(Spacer(1, 6))

    # AI Scope Analysis
    if ai_analysis:
        elements.append(PageBreak())
        elements.append(Paragraph("AI Scope Analysis", header_style))
        try:
            completion = ai_analysis.get("completion", 0)
            elements.append(Paragraph(f"<b>Total Completion:</b> {round(completion)}%", normal))
            elements.append(Spacer(1, 6))

            for item in ai_analysis.get("scored_items", []):
                text = item.get("scope", "—")
                matched = item.get("match", False)
                confidence = item.get("confidence", 0)
                symbol = "✅" if matched else "❌"
                percent = f"{round(confidence)}%"
                elements.append(Paragraph(f"{symbol} {text} — {percent}", normal))

            if ai_analysis.get("out_of_scope"):
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("<b>Flagged as Out-of-Scope:</b>", normal))
                for oos in ai_analysis["out_of_scope"]:
                    elements.append(Paragraph(f"⚠️ {oos}", normal))

        except Exception as e:
            elements.append(Paragraph(f"⚠️ Error rendering AI scope analysis: {str(e)}", normal))

    # Safety Sheet
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(PageBreak())
        elements.append(Paragraph("Safety Sheet", header_style))
        if safety_sheet_path.lower().endswith((".jpg", ".jpeg", ".png")):
            elements.append(Image(safety_sheet_path, width=5.5*inch, height=7*inch))
        else:
            elements.append(Paragraph(f"Attached: {os.path.basename(safety_sheet_path)}", normal))

    # Build PDF
    doc.build(elements)
