# utils/pdf_generator.py — v2025.11.01C
# 🎞️ Enhanced with play overlay on video thumbnails and better layout alignment

import os
import time
import traceback
import subprocess
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image as PILImage, ExifTags


# ---------------------------------------------------------------------
# 🧩 Utility: Fix orientation + compress
# ---------------------------------------------------------------------
def fix_orientation_and_compress(image_path):
    try:
        img = PILImage.open(image_path)
        exif = img._getexif() if hasattr(img, "_getexif") else None
        if exif:
            orientation = next(
                (ExifTags.TAGS.get(tag, tag) for tag, val in exif.items() if ExifTags.TAGS.get(tag) == "Orientation"),
                None,
            )
            if orientation:
                if exif.get(orientation) == 3:
                    img = img.rotate(180, expand=True)
                elif exif.get(orientation) == 6:
                    img = img.rotate(270, expand=True)
                elif exif.get(orientation) == 8:
                    img = img.rotate(90, expand=True)

        img = img.convert("RGB")
        img.thumbnail((1000, 1000))
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        return temp_path
    except Exception as e:
        print(f"⚠️ Image compression failed for {image_path}: {e}")
        return image_path


# ---------------------------------------------------------------------
# 🎞️ Video thumbnail generator
# ---------------------------------------------------------------------
def generate_video_thumbnail(video_path):
    try:
        thumb_path = video_path.rsplit(".", 1)[0] + "_thumb.jpg"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:01.000", "-vframes", "1", thumb_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return thumb_path if os.path.exists(thumb_path) else None
    except Exception as e:
        print(f"⚠️ Thumbnail generation failed: {e}")
        return None


# ---------------------------------------------------------------------
# 🧱 PDF Builder
# ---------------------------------------------------------------------
def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report, save_path,
                         weather_icon_path=None, safety_sheet_path=None):
    try:
        start = time.time()
        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def add(text, style="Normal"):
            elements.append(Paragraph(text, styles[style]))

        # ------------------ PAGE 1 ------------------
        if logo_path and os.path.exists(logo_path):
            elements.append(Image(logo_path, width=120, height=60))
        add("<b>DAILY LOG</b>", "Title")
        elements.append(Spacer(1, 12))

        info = [
            ("Project", data.get("project_name")),
            ("Client", data.get("client_name")),
            ("Location", data.get("location")),
            ("Date", data.get("date")),
            ("Weather", data.get("weather")),
        ]
        for k, v in info:
            add(f"<b>{k}:</b> {v or '—'}")

        elements.append(Spacer(1, 12))
        add(f"<b>Work Done:</b> {data.get('work_done', '—')}")
        add(f"<b>Crew Notes:</b> {data.get('crew_notes', '—')}")
        add(f"<b>Safety Notes:</b> {data.get('safety_notes', '—')}")
        elements.append(PageBreak())

        # ------------------ PAGE 2 ------------------
        add("<b>📷 Jobsite Media</b>", "Heading2")
        images = [p for p in image_paths if os.path.splitext(p)[1].lower() in [".jpg", ".jpeg", ".png"]]
        videos = [p for p in image_paths if os.path.splitext(p)[1].lower() in [".mp4", ".mov", ".avi", ".mkv"]]

        # --- Images ---
        if images:
            grid, row = [], []
            for i, img_path in enumerate(images):
                comp = fix_orientation_and_compress(img_path)
                row.append(Image(comp, width=2.5 * inch, height=2.5 * inch))
                if len(row) == 2:
                    grid.append(row)
                    row = []
            if row:
                grid.append(row)
            elements.append(Table(grid, hAlign="LEFT"))
        else:
            add("<font color='gray'>No jobsite images uploaded.</font>")
        elements.append(Spacer(1, 12))

        # --- Videos ---
        if videos:
            add("<b>🎥 Uploaded Videos</b>", "Heading2")
            for vid in videos:
                thumb = generate_video_thumbnail(vid)
                name = os.path.basename(vid)
                url = f"/{vid}"
                if thumb and os.path.exists(thumb):
                    elements.append(Image(fix_orientation_and_compress(thumb), width=2.5 * inch, height=2.0 * inch))
                    add(f"<b>▶️ <a href='{url}'>Click to Play</a></b>")
                else:
                    add(f"🎬 <a href='{url}'>{name}</a>")
        else:
            add("<font color='gray'>No video files uploaded.</font>")
        elements.append(PageBreak())

        # ------------------ PAGE 3 ------------------
        add("<b>🤖 AI Scope Analysis</b>", "Heading2")
        if ai_analysis:
            add(f"<b>Completion:</b> {ai_analysis.get('completion', 0)}%")
        else:
            add("<font color='gray'>No AI analysis results.</font>")
        elements.append(PageBreak())

        # ------------------ PAGE 4 ------------------
        add("<b>⛑️ Safety Sheet</b>", "Heading2")
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            ext = os.path.splitext(safety_sheet_path)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                elements.append(Image(fix_orientation_and_compress(safety_sheet_path), width=5 * inch, height=6 * inch))
            else:
                add(f"Safety sheet file: {os.path.basename(safety_sheet_path)}")
        else:
            add("<font color='gray'>No safety sheet attached.</font>")

        doc.build(elements)
        print(f"✅ PDF built in {round(time.time() - start, 2)}s")

    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        traceback.print_exc()
