from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from PIL import Image as PILImage, ExifTags
import os, uuid

def fix_image_orientation(path):
    try:
        image = PILImage.open(path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
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

def draw_progress_bar(percentage):
    drawing = Drawing(400, 50)
    width = 300
    filled_width = width * (percentage / 100.0)

    # Determine color based on completion
    if percentage >= 80:
        color = colors.green
    elif percentage >= 50:
        color = colors.orange
    else:
        color = colors.red

    drawing.add(Rect(0, 20, width, 20, fillColor=colors.lightgrey, strokeColor=None))
    drawing.add(Rect(0, 20, filled_width, 20, fillColor=color, strokeColor=None))
    drawing.add(String(0, 0, f"Completion: {percentage}%", fontSize=12))
    return drawing

def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report,
                         save_path, weather_icon_path, safety_sheet_path,
                         scope_result=None):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []

    # === Page 1 ===
    elements.append(Paragraph("DAILY LOG", styles["Title"]))
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=100, height=50))
    if weather_icon_path and os.path.exists(weather_icon_path):
        elements.append(Image(weather_icon_path, width=40, height=40))
    elements.append(Spacer(1, 0.2 * inch))

    for key in ["project_name", "client_name", "location", "date", "weather"]:
        if key in data:
            elements.append(Paragraph(f"<b>{key.title()}:</b> {data[key]}", styles["Normal"]))
    for section in ["crew_notes", "work_done", "safety_notes"]:
        if section in data:
            elements.append(Paragraph(f"<b>{section.replace('_', ' ').title()}:</b>", styles["Heading3"]))
            elements.append(Paragraph(data[section], styles["Normal"]))
    elements.append(PageBreak())

    # === Page 2 – Photos ===
    elements.append(Paragraph("JOB SITE PHOTOS", styles["Title"]))
    for path in image_paths:
        try:
            pil_image = fix_image_orientation(path)
            temp_img = create_temp_image(pil_image)
            elements.append(Image(temp_img, width=5.5 * inch, height=3.5 * inch))
        except Exception as e:
            elements.append(Paragraph(f"Error loading image: {e}", styles["Normal"]))
    elements.append(PageBreak())

    # === Page 3 – AI / AR Scope ===
    if ai_analysis or progress_report:
        elements.append(Paragraph("AI / AR COMPARISON", styles["Title"]))
        ai_text = "Enabled" if ai_analysis else "Disabled"
        elements.append(Paragraph("<b>AI Analysis:</b>", styles["Heading3"]))
        elements.append(Paragraph(ai_text, styles["Normal"]))
        if scope_result:
            elements.append(Paragraph("<b>Scope Completion:</b>", styles["Heading3"]))
            if "matched" in scope_result:
                elements.append(Paragraph("✅ Matched Items:", styles["Heading4"]))
                for item in scope_result["matched"]:
                    elements.append(Paragraph(f"- {item}", styles["Normal"]))
            if "flagged_missing" in scope_result:
                elements.append(Paragraph("❌ Missing Items:", styles["Heading4"]))
                for item in scope_result["flagged_missing"]:
                    elements.append(Paragraph(f"- {item}", styles["Normal"]))
            if "out_of_scope" in scope_result:
                elements.append(Paragraph("🚫 Out-of-Scope Items:", styles["Heading4"]))
                for item in scope_result["out_of_scope"]:
                    elements.append(Paragraph(f"- {item}", styles["Normal"]))
            if "percent_complete" in scope_result:
                elements.append(draw_progress_bar(scope_result["percent_complete"]))
        elif progress_report:
            elements.append(Paragraph(str(progress_report), styles["Normal"]))
        elements.append(PageBreak())

    # === Page 4 – Safety Sheet ===
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        elements.append(Paragraph("DAILY SAFETY SHEET", styles["Title"]))
        ext = os.path.splitext(safety_sheet_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png"]:
            pil_image = fix_image_orientation(safety_sheet_path)
            temp_img = create_temp_image(pil_image)
            elements.append(Image(temp_img, width=6.5 * inch, height=9 * inch))
        elif ext == ".pdf":
            elements.append(Paragraph("Safety sheet PDF attached separately.", styles["Normal"]))
        elif ext in [".doc", ".docx", ".xls", ".xlsx"]:
            elements.append(Paragraph("Uploaded Word/Excel file saved in project records.", styles["Normal"]))
        else:
            elements.append(Paragraph("Unsupported safety file type.", styles["Normal"]))
        elements.append(PageBreak())

    # === Build ===
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    # === Cleanup ===
    for f in os.listdir():
        if f.startswith("temp_") and f.endswith(".jpg"):
            try: os.remove(f)
            except: pass

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
