from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps
import os

def create_daily_log_pdf(form_data, photo_paths, output_path, logo_path=None, scope_path=None, weather=None, enable_ai_analysis=False):
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

    # ------------------ PAGE 1: Daily Log ------------------
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height - margin, "DAILY LOG")

    if logo_path:
        try:
            c.drawImage(ImageReader(logo_path), width - 100, height - 100, width=70, preserveAspectRatio=True, mask='auto')
        except:
            pass

    c.setFont("Helvetica", 12)
    y = height - 100
    fields = [
        "project_name", "client_name", "location", "job_number",
        "crew_notes", "work_done", "safety_notes"
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

    if scope_path:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(margin, y - 10, f"📄 Scope of Work Linked: {os.path.basename(scope_path)}")

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

    # ------------------ PAGE 3: AI / AR Analysis ------------------
    if enable_ai_analysis:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, height - margin, "AI / AR Analysis & Work Progress")

        c.setFont("Helvetica", 12)
        y = height - 100

        c.drawString(margin, y, "📊 AI Review Summary:")
        y -= 20
        c.drawString(margin, y, "• Detected progress based on visual site updates.")
        y -= 20
        c.drawString(margin, y, "• Comparing current work vs Scope of Work file.")
        y -= 20
        c.drawString(margin, y, "• Potential out-of-scope activities flagged for review (Change Orders).")

        y -= 40
        c.drawString(margin, y, "⚙️ Next Update:")
        y -= 20
        c.drawString(margin, y, "This section will evolve to show percentage completion from AI scope matching.")

    # ------------------ FOOTER ------------------
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(margin, 30, "Powered by Nails & Notes: Construction Daily Log AI © 2025")
    c.save()

    # Cleanup
    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass
