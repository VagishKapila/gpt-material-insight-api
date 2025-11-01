import os
import time
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage, ExifTags


def fix_orientation_and_compress(image_path):
    """Auto-rotate, resize, and compress an image safely with EXIF support."""
    try:
        start = time.time()
        img = PILImage.open(image_path)

        # ✅ Auto-rotate based on EXIF orientation
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
                        print(f"↻ Rotated image {os.path.basename(image_path)} (orientation={value})")
                        break
        except Exception as e:
            print(f"⚠️ Could not read EXIF for {image_path}: {e}")

        img = img.convert("RGB")
        img.thumbnail((1000, 1000))  # keep aspect ratio
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        print(f"🖼️ Processed image {os.path.basename(image_path)} in {round(time.time() - start, 2)}s")
        return temp_path
    except Exception as e:
        print(f"❌ Failed to process {image_path}: {e}")
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
    """Builds a complete multi-page PDF with rotation and scaling fixes."""
    try:
        print("\n🚧 Starting PDF generation...")
        print(f"📸 Total image_paths: {len(image_paths)}")

        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        start_time = time.time()

        def add_paragraph(text, style="Normal"):
            elements.append(Paragraph(text, styles[style]))

        # --- PAGE 1: DAILY LOG ---
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

        # --- PAGE 2: JOBSITE PHOTOS ---
        valid_images = [p for p in image_paths if p.lower().endswith((".jpg", ".jpeg", ".png"))]
        if valid_images:
            add_paragraph("<b>📷 Jobsite Photos</b>", "Heading2")
            photo_table, row = [], []
            for idx, img_path in enumerate(valid_images):
                print(f"🔍 [{idx+1}/{len(valid_images)}] {img_path}")
                try:
                    compressed = fix_orientation_and_compress(img_path)
                    img = Image(compressed, width=2.5 * inch, height=2.5 * inch)
                    row.append(img)
                    if len(row) == 2:
                        photo_table.append(row)
                        row = []
                except Exception as e:
                    print(f"⚠️ Error embedding {img_path}: {e}")
                    continue
            if row:
                photo_table.append(row)
            if photo_table:
                elements.append(Table(photo_table, hAlign="LEFT"))
            elements.append(PageBreak())
        else:
            print("⚠️ No valid image files found for PDF (videos ignored).")

        # --- PAGE 3: AI ANALYSIS ---
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
                                img = Image(fix_orientation_and_compress(path), width=2.5 * inch, height=2.5 * inch)
                                elements.append(img)
                                break
                            except Exception as e:
                                print(f"⚠️ Failed to load matched image: {e}")
                else:
                    add_paragraph('<font color="gray">(No matched image provided)</font>')
                elements.append(Spacer(1, 10))

            out_items = ai_analysis.get("out_of_scope", [])
            if out_items:
                add_paragraph("<b>Out-of-Scope Items:</b>", "Heading3")
                for line in out_items:
                    add_paragraph(f"<font color='red'>• {line}</font>")
            elements.append(PageBreak())

        # --- PAGE 4: SAFETY SHEET ---
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            add_paragraph("📎 Attached Safety Sheet", "Heading2")
            try:
                ext = os.path.splitext(safety_sheet_path)[1].lower()
                if ext in [".jpg", ".jpeg", ".png"]:
                    img = Image(fix_orientation_and_compress(safety_sheet_path), width=5 * inch, height=6 * inch)
                    elements.append(img)
                else:
                    add_paragraph(
                        f"Safety sheet file: {os.path.basename(safety_sheet_path)} (non-image format)"
                    )
            except Exception as e:
                add_paragraph(f"⚠️ Could not load safety sheet: {e}")

        # --- BUILD PDF ---
        print(f"📝 Building PDF at {save_path}")
        doc.build(elements)
        print(f"✅ PDF built successfully in {round(time.time() - start_time, 2)}s")

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        traceback.print_exc()
