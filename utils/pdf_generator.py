from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps
import os

def create_daily_log_pdf(form_data, photo_paths, output_path, logo_path=None, weather=None, enable_ai_analysis=False):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    margin = 50
    temp_files = []

    def compress_and_correct_image(image_path):
        try:
            img = Image.open(image_path)
            img = ImageOps.exif_transpose(img)
            img.thumbnail((1200, 1200))
            temp_path = os.path.splitext(image_path)[0] + "_compressed.jpg"
            img.convert('RGB').save(temp_path, "JPEG", quality=40)
            temp_files.append(temp_path)
            return temp_path
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return image_path

    # ------------------ PAGE 1: Daily Log Header ------------------
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height - margin, "DAILY LOG")

    if logo_path:
        try:
            c.drawImage(ImageReader(logo_path), width - 100, height - 100, width=70, preserveAspectRatio=True, mask='auto')
        except:
            pass

    c.setFont("Helvetica", 12)
    y = height - 80
    fields = [
        "project_name", "client_name", "location", "job_number", "gc_name",
        "crew_notes", "work_done", "safety_notes", "equipment_used"
    ]

    for field in fields:
        value = form_data.get(field, "")
        if value:
            label = field.replace("_", " ").title()
            c.drawString(margin, y, f"{label}: {value}")
            y -= 18
            if y < margin:
                c.showPage()
                y = height - margin

    if weather:
        c.drawString(margin, y, f"Weather: {weather}")
        y -= 18

    c.showPage()

    # ------------------ PAGE 2: Job Site Photos ------------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, "Job Site Photos")

    x = margin
    y = height - 80
    photo_width = 250
    photo_height = 180
    spacing = 20

    for i, path in enumerate(photo_paths):
        compressed = compress_and_correct_image(path)
        try:
            c.drawImage(compressed, x, y, width=photo_width, height=photo_height, preserveAspectRatio=True)
            x += photo_width + spacing
            if x + photo_width > width:
                x = margin
                y -= photo_height + spacing
                if y < margin:
                    c.showPage()
                    y = height - margin
        except Exception as e:
            print(f"Error drawing photo {compressed}: {e}")

    c.showPage()

    # ------------------ PAGE 3: AI / Material Analysis ------------------
    if enable_ai_analysis:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, height - margin, "AI / AR Analysis & Material Comparison")

        c.setFont("Helvetica", 12)
        y = height - 100

        # Example placeholder data — this would later be replaced by GPT/AI output
        c.drawString(margin, y, "🔍 Detected Material: Sheetrock (Drywall)")
        y -= 20
        c.drawString(margin, y, "💲 Lowe’s - $8/sheet")
        y -= 20
        c.drawString(margin, y, "💲 Home Depot - $8.75/sheet")
        y -= 40
        c.drawString(margin, y, "📐 Suggested Measurement Overlay: 12ft × 8ft wall section")
        y -= 40
        c.drawString(margin, y, "📌 Tip: Replace water-damaged panels within 48 hrs of exposure.")
        y -= 20

        if y < margin:
            c.showPage()

    # ------------------ SAVE & CLEANUP ------------------
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margin, 30, "Powered by Nails & Notes: Construction Daily Log AI")
    c.save()

    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass
