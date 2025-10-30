import os
from PIL import Image as PILImage, ExifTags
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def fix_orientation_and_compress(image_path):
    try:
        img = PILImage.open(image_path)
        img = img.convert("RGB")
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif and orientation in exif:
                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    img = img.rotate(90, expand=True)
        except:
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

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(40, 20, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
        canvas.drawRightString(550, 20, f"Page {doc.page}")
        canvas.restoreState()

    # Page 1: Header
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=40))

    elements.append(Paragraph("<b>Daily Log Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    for key, value in data.items():
        elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles["Normal"]))
        elements.append(Spacer(1, 6))

    elements.append(PageBreak())

    # Page 2+: Jobsite Photos (6 per page)
    elements.append(Paragraph("<b>📸 Jobsite Photos</b>", styles["Heading2"]))
    photo_counter = 0
    for i, path in enumerate(image_paths):
        if os.path.exists(path):
            if photo_counter % 6 == 0 and photo_counter != 0:
                elements.append(PageBreak())
            img_path = fix_orientation_and_compress(path)
            elements.append(Image(img_path, width=3.5*inch, height=2.5*inch))
            elements.append(Spacer(1, 6))
            photo_counter += 1
    if photo_counter > 0:
        elements.append(PageBreak())

    # Page 3: AI Analysis
    elements.append(Paragraph("<b>🔍 AI Scope Analysis</b>", styles["Heading2"]))
    if ai_analysis:
        comp = ai_analysis.get("completion", 0)
        elements.append(Paragraph(f"<b>Estimated Completion:</b> {comp}%", styles["Normal"]))
        elements.append(Spacer(1, 6))
        for item in ai_analysis.get("scored_items", []):
            elements.append(Paragraph(f"<b>Scope:</b> {item['scope']}", styles["Normal"]))
            elements.append(Paragraph(
                f"✅ Match: {'Yes' if item['match'] else 'No'} — 🎯 Confidence: {item['confidence']}%",
                styles["Normal"]
            ))
            if item.get("matched_image") and os.path.exists(item["matched_image"]):
                try:
                    img_path = fix_orientation_and_compress(item["matched_image"])
                    elements.append(Image(img_path, width=3*inch, height=2.5*inch))
                except:
                    elements.append(Paragraph("⚠️ Failed to load matched image.", styles["Normal"]))
            elements.append(Spacer(1, 12))

    elements.append(PageBreak())

    # Page 4: Safety Sheet
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("<b>🦺 Safety Sheet</b>", styles["Heading2"]))
        try:
            img_path = fix_orientation_and_compress(safety_sheet_path)
            elements.append(Image(img_path, width=5*inch, height=6*inch))
        except:
            elements.append(Paragraph("⚠️ Unable to load safety image.", styles["Normal"]))

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
