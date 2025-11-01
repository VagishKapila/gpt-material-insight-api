# utils/pdf_generator.py — v2025.11.01
# Stable build with 🎞️ video thumbnail support, 🖼️ image compression, and full debug tracing

import os
import time
import traceback
import subprocess
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage, ExifTags


# ---------------------------------------------------------------------
# 🧩 Utility: Fix orientation + compress
# ---------------------------------------------------------------------
def fix_orientation_and_compress(image_path):
    """Auto‑rotate, resize, and compress an image safely with EXIF support."""
    try:
        start = time.time()
        img = PILImage.open(image_path)

        # ✅ Rotate using EXIF orientation tag
        try:
            exif = img._getexif()
            if exif:
                for tag, value in exif.items():
                    key = ExifTags.TAGS.get(tag, tag)
                    if key == "Orientation":
                        if value == 3:
                            img = img.rotate(180, expand=True)
                        elif value == 6:
                            img = img.rotate(270, expand=True)
                        elif value == 8:
                            img = img.rotate(90, expand=True)
                        print(f"↻ Rotated {os.path.basename(image_path)} (orientation={value})")
                        break
        except Exception as e:
            print(f"⚠️ No EXIF orientation info for {image_path}: {e}")

        img = img.convert("RGB")
        img.thumbnail((1000, 1000))  # Maintain aspect ratio
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        print(f"🖼️ Compressed {os.path.basename(image_path)} in {round(time.time() - start, 2)}s")
        return temp_path

    except Exception as e:
        print(f"❌ Image processing failed for {image_path}: {e}")
        return image_path


# ---------------------------------------------------------------------
# 🎞️ Utility: Generate a video thumbnail using FFmpeg
# ---------------------------------------------------------------------
def generate_video_thumbnail(video_path):
    """
    Extracts a still frame from the video (1s mark) as a JPG thumbnail.
    Returns the path of the thumbnail, or None if generation fails.
    """
    try:
        thumb_path = video_path.rsplit(".", 1)[0] + "_thumb.jpg"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:01.000", "-vframes", "1", thumb_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if os.path.exists(thumb_path):
            print(f"🎞️ Generated video thumbnail: {thumb_path}")
            return thumb_path
        else:
            print(f"⚠️ FFmpeg did not create a thumbnail for {video_path}. stderr:\n{result.stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ FFmpeg thumbnail generation failed for {video_path}: {e}")
        return None


# ---------------------------------------------------------------------
# 🧱 Core: Build Daily Log PDF
# ---------------------------------------------------------------------
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
    """
    Builds a clean, multi‑page PDF with:
      • Page 1: Daily Log Information
      • Page 2: Jobsite Photos + Video Thumbnails
      • Page 3: AI Scope Analysis
      • Page 4: Safety Sheet
    """
    try:
        print("\n🚧 Starting PDF generation ...")
        start_time = time.time()
        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def add_paragraph(text, style="Normal"):
            elements.append(Paragraph(text, styles[style]))

        # -----------------------------------------------------------------
        # PAGE 1 — DAILY LOG
        # -----------------------------------------------------------------
        print("📝 Building Page 1 (Daily Log Info)")
        if logo_path and os.path.exists(logo_path):
            elements.append(Image(logo_path, width=120, height=60))
        add_paragraph("<b>DAILY LOG</b>", "Title")
        elements.append(Spacer(1, 12))

        info_fields = [
            ("Project", data.get("project_name")),
            ("Client", data.get("client_name")),
            ("Location", data.get("location")),
            ("Date", data.get("date")),
            ("Weather", data.get("weather")),
        ]
        for label, val in info_fields:
            add_paragraph(f"<b>{label}:</b> {val or '—'}")

        elements.append(Spacer(1, 12))
        add_paragraph(f"<b>Work Done:</b> {data.get('work_done', '—')}")
        add_paragraph(f"<b>Crew Notes:</b> {data.get('crew_notes', '—')}")
        add_paragraph(f"<b>Safety Notes:</b> {data.get('safety_notes', '—')}")
        elements.append(PageBreak())

        # -----------------------------------------------------------------
        # PAGE 2 — JOBSITE MEDIA
        # -----------------------------------------------------------------
        print("📸 Building Page 2 (Jobsite Photos + Videos)")
        valid_images, valid_videos = [], []

        for p in image_paths:
            ext = os.path.splitext(p)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                valid_images.append(p)
            elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
                valid_videos.append(p)

        # --- Images
        if valid_images:
            add_paragraph("<b>📷 Jobsite Photos</b>", "Heading2")
            photo_table, row = [], []
            for idx, img_path in enumerate(valid_images):
                print(f"🖼️ Adding image {idx + 1}/{len(valid_images)}: {img_path}")
                try:
                    compressed = fix_orientation_and_compress(img_path)
                    img = Image(compressed, width=2.5 * inch, height=2.5 * inch)
                    row.append(img)
                    if len(row) == 2:
                        photo_table.append(row)
                        row = []
                except Exception as e:
                    print(f"⚠️ Skipped image {img_path}: {e}")
            if row:
                photo_table.append(row)
            if photo_table:
                elements.append(Table(photo_table, hAlign="LEFT"))
        else:
            add_paragraph("<font color='gray'>No jobsite images uploaded.</font>")

        elements.append(Spacer(1, 12))

        # --- Videos
        if valid_videos:
            add_paragraph("<b>🎥 Uploaded Videos</b>", "Heading2")
            for vid in valid_videos:
                print(f"🎞️ Processing video: {vid}")
                thumb_path = generate_video_thumbnail(vid)
                video_name = os.path.basename(vid)
                video_url = f"/{vid}" if not vid.startswith("http") else vid

                if thumb_path and os.path.exists(thumb_path):
                    try:
                        img = Image(thumb_path, width=2.5 * inch, height=2.0 * inch)
                        elements.append(img)
                        add_paragraph(f"▶️ <a href='{video_url}'>{video_name}</a>", "Normal")
                    except Exception as e:
                        print(f"⚠️ Could not embed video thumbnail: {e}")
                        add_paragraph(f"🎬 <a href='{video_url}'>{video_name}</a>", "Normal")
                else:
                    add_paragraph(f"🎬 <a href='{video_url}'>{video_name}</a>", "Normal")
        else:
            print("⚠️ No video files found for PDF.")

        elements.append(PageBreak())

        # -----------------------------------------------------------------
        # PAGE 3 — AI SCOPE ANALYSIS
        # -----------------------------------------------------------------
        print("🧠 Building Page 3 (AI Scope Analysis)")
        if ai_analysis:
            completion = ai_analysis.get("completion", 0)
            add_paragraph("🤖 AI Scope Comparison", "Heading2")
            add_paragraph(f"<b>Estimated Completion:</b> {completion}%")
            elements.append(Spacer(1, 12))

            for item in ai_analysis.get("scored_items", []):
                scope = item.get("scope", "")
                conf = item.get("confidence", 0)
                match = item.get("match", False)
                matched_image = item.get("matched_image")

                add_paragraph(
                    f"<b>Scope:</b> {scope}<br/><b>Confidence:</b> {conf}%<br/><b>Match:</b> {'✅' if match else '❌'}"
                )
                elements.append(Spacer(1, 6))

                if matched_image:
                    possible_paths = [
                        os.path.join("static/uploads", matched_image),
                        os.path.join("static/uploads", matched_image.replace("_compressed", "")),
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            try:
                                elements.append(
                                    Image(fix_orientation_and_compress(path), width=2.5 * inch, height=2.5 * inch)
                                )
                                break
                            except Exception as e:
                                print(f"⚠️ Could not load matched image: {e}")
                elements.append(Spacer(1, 10))

            out_items = ai_analysis.get("out_of_scope", [])
            if out_items:
                add_paragraph("<b>Out-of-Scope Items:</b>", "Heading3")
                for line in out_items:
                    add_paragraph(f"<font color='red'>• {line}</font>")
        else:
            add_paragraph("<font color='gray'>No AI analysis data found.</font>")
        elements.append(PageBreak())

        # -----------------------------------------------------------------
        # PAGE 4 — SAFETY SHEET
        # -----------------------------------------------------------------
        print("⛑️ Building Page 4 (Safety Sheet)")
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            add_paragraph("📎 Attached Safety Sheet", "Heading2")
            try:
                ext = os.path.splitext(safety_sheet_path)[1].lower()
                if ext in [".jpg", ".jpeg", ".png"]:
                    elements.append(
                        Image(fix_orientation_and_compress(safety_sheet_path), width=5 * inch, height=6 * inch)
                    )
                else:
                    add_paragraph(
                        f"Safety sheet file: {os.path.basename(safety_sheet_path)} (non-image format)"
                    )
            except Exception as e:
                add_paragraph(f"⚠️ Could not load safety sheet: {e}")
        else:
            add_paragraph("<font color='gray'>No safety sheet attached.</font>")

        # -----------------------------------------------------------------
        # FINAL BUILD
        # -----------------------------------------------------------------
        print(f"📝 Building PDF at: {save_path}")
        doc.build(elements)
        print(f"✅ PDF generated successfully in {round(time.time() - start_time, 2)}s")

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        traceback.print_exc()
