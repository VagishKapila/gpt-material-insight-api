import os
from utils.video_tools import generate_video_thumbnail
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

        # ✅ Rotate using EXIF
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
            print(f"⚠️ No EXIF orientation for {image_path}: {e}")

        img = img.convert("RGB")
        img.thumbnail((1000, 1000))
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        print(f"🖼️ Processed {os.path.basename(image_path)} in {round(time.time() - start, 2)}s")
        return temp_path

    except Exception as e:
        print(f"❌ Failed to process {image_path}: {e}")
        return image_path


# ---------------------------------------------------------------------
# 🎞️ Utility: Extract thumbnail from video (fallback safe)
# ---------------------------------------------------------------------
def generate_video_thumbnail(video_path):
    """Create a still thumbnail from a video using FFmpeg; returns image path."""
    try:
        thumb_path = video_path.rsplit(".", 1)[0] + "_thumb.jpg"
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-ss", "00:00:01.000", "-vframes", "1", thumb_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(thumb_path):
            print(f"🎞️ Generated thumbnail: {thumb_path}")
            return thumb_path
        else:
            print(f"⚠️ FFmpeg did not create thumbnail for {video_path}")
            return None
    except Exception as e:
        print(f"⚠️ Thumbnail generation failed for {video_path}: {e}")
        return None


# ---------------------------------------------------------------------
# 🧱 Core: Build PDF
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
    """Build a complete PDF with job photos, video thumbnails, AI analysis."""
    try:
        print("\n🚧 Starting PDF generation...")
        start_time = time.time()
        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def add_paragraph(text, style="Normal"):
            elements.append(Paragraph(text, styles[style]))

        # -----------------------------------------------------------------
        # PAGE 1 – Daily Log Info
        # -----------------------------------------------------------------
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
        # PAGE 2 – Jobsite Photos + Videos
        # -----------------------------------------------------------------
        print("🧩 Building jobsite media section...")
        valid_images = []
        valid_videos = []

        for p in image_paths:
            ext = os.path.splitext(p)[1].lower()
            if ext in [".jpg", ".jpeg", ".png"]:
                valid_images.append(p)
            elif ext in [".mp4", ".mov", ".avi"]:
                valid_videos.append(p)

        # ---- Images
        if valid_images:
            add_paragraph("<b>📷 Jobsite Photos</b>", "Heading2")
            photo_table, row = [], []
            for idx, img_path in enumerate(valid_images):
                try:
                    compressed = fix_orientation_and_compress(img_path)
                    img = Image(compressed, width=2.5 * inch, height=2.5 * inch)
                    row.append(img)
                    if len(row) == 2:
                        photo_table.append(row)
                        row = []
                except Exception as e:
                    print(f"⚠️ Image skipped: {img_path} ({e})")
            if row:
                photo_table.append(row)
            if photo_table:
                elements.append(Table(photo_table, hAlign="LEFT"))
        else:
            print("⚠️ No image files in this session.")

        # ---- Videos
        if valid_videos:
            add_paragraph("<b>🎞️ Uploaded Videos</b>", "Heading2")
            for vid in valid_videos:
                thumb = generate_video_thumbnail(vid)
                video_name = os.path.basename(vid)
                video_url = f"/{vid}" if not vid.startswith("http") else vid
                if thumb and os.path.exists(thumb):
                    try:
                        elements.append(Image(thumb, width=2.5 * inch, height=2.0 * inch))
                        add_paragraph(f'<a href="{video_url}">{video_name}</a>', "Normal")
                    except Exception as e:
                        print(f"⚠️ Could not embed thumbnail: {e}")
                        add_paragraph(f'<a href="{video_url}">{video_name}</a>', "Normal")
                else:
                    add_paragraph(f'🎥 <a href="{video_url}">{video_name}</a>', "Normal")

        elements.append(PageBreak())

        # -----------------------------------------------------------------
        # PAGE 3 – AI Scope Analysis
        # -----------------------------------------------------------------
        if ai_analysis:
            add_paragraph("🤖 AI Scope Comparison", "Heading2")
            completion = ai_analysis.get("completion", 0)
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
                                print(f"⚠️ Failed to load matched image: {e}")
                elements.append(Spacer(1, 10))

            out_items = ai_analysis.get("out_of_scope", [])
            if out_items:
                add_paragraph("<b>Out-of-Scope Items:</b>", "Heading3")
                for line in out_items:
                    add_paragraph(f"<font color='red'>• {line}</font>")
            elements.append(PageBreak())

        # -----------------------------------------------------------------
        # PAGE 4 – Safety Sheet
        # -----------------------------------------------------------------
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            add_paragraph("📎 Attached Safety Sheet", "Heading2")
            try:
                ext = os.path.splitext(safety_sheet_path)[1].lower()
                if ext in [".jpg", ".jpeg", ".png"]:
                    elements.append(Image(fix_orientation_and_compress(safety_sheet_path), width=5 * inch, height=6 * inch))
                else:
                    add_paragraph(f"Safety sheet file: {os.path.basename(safety_sheet_path)} (non-image format)")
            except Exception as e:
                add_paragraph(f"⚠️ Could not load safety sheet: {e}")

        # -----------------------------------------------------------------
        # BUILD
        # -----------------------------------------------------------------
        print(f"📝 Building PDF at {save_path}")
        doc.build(elements)
        print(f"✅ PDF built successfully in {round(time.time() - start_time, 2)}s")

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        traceback.print_exc()
