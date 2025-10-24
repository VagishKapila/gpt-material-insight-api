from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from PyPDF2 import PdfMerger
from PIL import Image, ImageOps
import os

def create_daily_log_pdf(data, image_paths, logo_path=None, ai_analysis=None,
                         progress_report=None, save_path="daily_log.pdf",
                         weather_icon_path=None, safety_sheet_path=None):
    temp_files = []

    # --- Page 1: Daily Log Metadata ---
    page1_path = save_path.replace(".pdf", "_page1.pdf")
    c = canvas.Canvas(page1_path, pagesize=letter)
    width, height = letter

    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path)
            logo_img = ImageOps.exif_transpose(logo_img)
            logo_img.thumbnail((120, 120))
            logo_img.save("temp_logo.png")
            c.drawImage("temp_logo.png", inch, height - 1.5 * inch, width=1.5 * inch, preserveAspectRatio=True)
            temp_files.append("temp_logo.png")
        except Exception as e:
            print(f"⚠️ Error embedding logo: {e}")

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - inch, "DAILY LOG")

    # Project Metadata
    c.setFont("Helvetica", 12)
    y = height - 2 * inch
    for key in ["project_name", "location", "date"]:
        if key in data:
            c.drawString(inch, y, f"{key.replace('_', ' ').title()}: {data[key]}")
            y -= 0.3 * inch

    # Weather
    if weather_icon_path and os.path.exists(weather_icon_path):
        try:
            c.drawImage(weather_icon_path, width - 1.5 * inch, height - 1.5 * inch, width=1 * inch, preserveAspectRatio=True)
        except Exception as e:
            print(f"⚠️ Error embedding weather icon: {e}")

    # Notes
    y -= 0.2 * inch
    for label in ["crew_notes", "work_done", "safety_notes"]:
        if data.get(label):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(inch, y, label.replace("_", " ").title() + ":")
            y -= 0.2 * inch
            c.setFont("Helvetica", 11)
            text = c.beginText(inch, y)
            text.setLeading(14)
            for line in data[label].split('\n'):
                text.textLine(line.strip())
            c.drawText(text)
            y = text.getY() - 0.3 * inch

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 0.5 * inch, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
    c.showPage()
    c.save()

    # --- Page 2: Images ---
    page2_path = save_path.replace(".pdf", "_page2.pdf")
    c = canvas.Canvas(page2_path, pagesize=letter)
    x, y = inch, height - inch
    max_w = 3.5 * inch
    max_h = 3.5 * inch

    for idx, img_path in enumerate(image_paths):
        try:
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img)
            img.thumbnail((max_w, max_h))
            safe_path = f"temp_img_{idx}.jpg"
            img.save(safe_path)
            temp_files.append(safe_path)

            c.drawImage(safe_path, x, y - img.height, width=img.width, height=img.height)

            x += max_w + 0.5 * inch
            if x + max_w > width:
                x = inch
                y -= max_h + inch
                if y < inch:
                    c.showPage()
                    x, y = inch, height - inch
        except Exception as e:
            print(f"⚠️ Failed to embed image {img_path}: {e}")
            continue

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 0.5 * inch, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
    c.showPage()
    c.save()

    # --- Page 3: AI Analysis / Scope Progress ---
    page3_path = save_path.replace(".pdf", "_page3.pdf")
    doc = SimpleDocTemplate(page3_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI & Scope Notes</b>", styles["Title"]))
    story.append(Spacer(1, 0.25 * inch))

    if ai_analysis:
        story.append(Paragraph("<b>AI Image Summary:</b><br/>" + ai_analysis, styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    if progress_report:
        story.append(Paragraph("<b>Scope Completion Progress:</b><br/>" + progress_report, styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story)

    # --- Page 4: Safety Sheet ---
    safety_path = save_path.replace(".pdf", "_page4.pdf")
    c = canvas.Canvas(safety_path, pagesize=letter)
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        try:
            ext = os.path.splitext(safety_sheet_path)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                img = Image.open(safety_sheet_path)
                img = ImageOps.exif_transpose(img)
                img.thumbnail((width - 2 * inch, height - 2 * inch))
                temp_safe = "temp_safety.jpg"
                img.save(temp_safe)
                temp_files.append(temp_safe)
                c.drawImage(temp_safe, inch, inch, width=img.width, height=img.height)
            else:
                c.setFont("Helvetica", 12)
                c.drawString(inch, height - inch, "🛠️ Safety file format not supported for preview (e.g., .pdf, .docx)")
        except Exception as e:
            print(f"❌ Error rendering safety sheet: {e}")
            c.setFont("Helvetica", 12)
            c.drawString(inch, height - inch, f"⚠️ Error loading safety sheet: {e}")
    else:
        c.setFont("Helvetica", 12)
        c.drawString(inch, height - inch, "❌ No safety sheet uploaded")

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 0.5 * inch, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
    c.showPage()
    c.save()

    # --- Merge All Pages ---
    merger = PdfMerger()
    for path in [page1_path, page2_path, page3_path, safety_path]:
        merger.append(path)
        temp_files.append(path)

    merger.write(save_path)
    merger.close()

    # Cleanup
    for f in temp_files:
        try:
            os.remove(f)
        except Exception:
            pass

    print(f"✅ PDF generated at: {save_path}")
