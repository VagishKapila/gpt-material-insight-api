from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ExifTags
import os

def create_daily_log_pdf(form_data, image_paths, output_path, logo_path=None):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    margin = 50

    def compress_and_correct_image(image_path):
        try:
            img = Image.open(image_path)

            # Auto-orient using EXIF
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = img._getexif()
                if exif is not None:
                    orientation_value = exif.get(orientation, None)
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
            except Exception as e:
                pass  # Ignore EXIF issues

            # Resize
            img.thumbnail((1600, 1600))

            # Convert to JPEG and compress
            temp_path = image_path + ".jpg"
            img.convert('RGB').save(temp_path, "JPEG", quality=50)
            return temp_path

        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return image_path

    # Header
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height - margin, "DAILY LOG")
    c.setFont("Helvetica", 12)

    if logo_path:
        try:
            c.drawImage(ImageReader(logo_path), width - 120, height - 100, width=70, preserveAspectRatio=True, mask='auto')
        except:
            pass

    y = height - 80
    for key in ["project_name", "location", "date", "crew_notes", "work_done", "safety_notes", "weather"]:
        if key in form_data:
            label = key.replace("_", " ").title()
            c.drawString(margin, y, f"{label}: {form_data.get(key)}")
            y -= 18

    c.showPage()

    # Images page
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - margin, "Job Site Photos")

    x = margin
    y = height - 80
    photo_width = 250
    photo_height = 180
    spacing = 20

    for i, original_path in enumerate(image_paths):
        compressed = compress_and_correct_image(original_path)
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
            print(f"Failed to draw image: {compressed}", e)

    c.save()

