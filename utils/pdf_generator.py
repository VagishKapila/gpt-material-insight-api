# ✅ Updated pdf_generator.py with debug logs and safe image handling
import os
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage

def fix_orientation_and_compress(image_path):
    try:
        img = PILImage.open(image_path)
        img = img.convert("RGB")
        img.thumbnail((800, 800))
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        return temp_path
    except Exception as e:
        print(f"⚠️ Failed to compress {image_path}: {e}")
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
    try:
        print("🚧 Starting PDF generation...")
        print(f"📸 Received image_paths: {image_paths}")

        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def add_paragraph(text, style="Normal"):
            elements.append(Paragraph(text, styles[style]))

        # --- Page 1: Daily Log Details ---
        if logo_path and os.path.exists(logo_path):
            elements.append(Image(logo_path, width=120, height=60))
        add_paragraph("<b>DAILY LOG</b>", "Title")
        elements.append(Spacer(1, 12))

        add_paragraph(f"<b>Project:</b> {data.get('project_name', '—')}")
        add_paragraph(f"<b>Client:</b> {data.get('client_name', '—')}")
        add_paragraph(f"<b>Location:</b> {data.get('location', '—')}")
        add_paragraph(f"<b>Date:</b> {data.get('date', '—')}")
        add_paragraph(f"<b>Weather:</b> {data.get('weather', '—')}")
        elements.append(Spacer(1, 12))

        add_paragraph(f"<b>Work Done:</b> {data.get('work_done', '—')}")
        add_paragraph(f"<b>Crew Notes:</b> {data.get('crew_notes', '—')}")
        add_paragraph(f"<b>Safety Notes:</b> {data.get('safety_notes', '—')}")
        elements.append(PageBreak())

        # --- Page 2: Jobsite Photos ---
        if image_paths:
            add_paragraph("<b>📷 Jobsite Photos</b>", "Heading2")
            photo_table = []
            row = []
            for idx, img_path in enumerate(image_paths):
                print(f"🔍 Processing image {idx+1}: {img_path}")
                try:
                    compressed = fix_orientation_and_compress(img_path)
                    img = Image(compressed, width=2.5 * inch, height=2.5 * inch)
                    row.append(img)
                    if len(row) == 2:
                        photo_table.append(row)
                        row = []
                except Exception as e:
                    print(f"⚠️ Error loading image: {e}")
                    continue
            if row:
                photo_table.append(row)
            elements.append(Table(photo_table, hAlign='LEFT'))
            elements.append(PageBreak())
        else:
            print("⚠️ No jobsite images to show on PDF.")

        # --- Page 3: AI Scope Analysis ---
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

                add_paragraph(f"<b>Scope:</b> {scope}<br/><b>Confidence:</b> {conf}%<br/><b>Match:</b> {'✅' if match else '❌'}")
                elements.append(Spacer(1, 6))

                if matched_image:
                    possible_paths = [
                        os.path.join("static/uploads", matched_image),
                        os.path.join("static/uploads", matched_image.replace("_compressed", ""))
                    ]
                    image_found = False
                    for path in possible_paths:
                        if os.path.exists(path):
                            try:
                                img = Image(fix_orientation_and_compress(path), width=2.5*inch, height=2.5*inch)
                                elements.append(img)
                                image_found = True
                                break
                            except Exception as e:
                                print(f"⚠️ Failed to load matched image: {e}")
                    if not image_found:
                        add_paragraph('<font color="red">⚠️ Matched image not found or failed to load.</font>')
                else:
                    add_paragraph('<font color="gray">(No matched image provided)</font>')
                elements.append(Spacer(1, 12))

            out_items = ai_analysis.get("out_of_scope", [])
            if out_items:
                add_paragraph("<b>Out-of-Scope Items:</b>", "Heading3")
                for line in out_items:
                    add_paragraph(f"<font color='red'>• {line}</font>")
            elements.append(PageBreak())

        # --- Page 4: Safety Sheet ---
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            try:
                ext = os.path.splitext(safety_sheet_path)[1].lower()
                if ext in [".jpg", ".jpeg", ".png"]:
                    add_paragraph("📎 Attached Safety Sheet", "Heading2")
                    elements.append(Image(fix_orientation_and_compress(safety_sheet_path), width=5*inch, height=6*inch))
                else:
                    add_paragraph("📎 Attached Safety Sheet: (non-image format, view file separately)", "Heading2")
            except Exception as e:
                print(f"⚠️ Error displaying safety sheet: {e}")
                add_paragraph("⚠️ Error displaying safety sheet.")

        # --- Final Build ---
        print(f"📝 Building PDF: {save_path}")
        doc.build(elements)
        print("✅ PDF successfully generated.")

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        traceback.print_exc()# ✅ Updated pdf_generator.py with debug logs and safe image handling
import os
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage

def fix_orientation_and_compress(image_path):
    try:
        img = PILImage.open(image_path)
        img = img.convert("RGB")
        img.thumbnail((800, 800))
        temp_path = image_path.replace(".jpg", "_compressed.jpg").replace(".png", "_compressed.png")
        img.save(temp_path, quality=70)
        return temp_path
    except Exception as e:
        print(f"⚠️ Failed to compress {image_path}: {e}")
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
    try:
        print("🚧 Starting PDF generation...")
        print(f"📸 Received image_paths: {image_paths}")

        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def add_paragraph(text, style="Normal"):
            elements.append(Paragraph(text, styles[style]))

        # --- Page 1: Daily Log Details ---
        if logo_path and os.path.exists(logo_path):
            elements.append(Image(logo_path, width=120, height=60))
        add_paragraph("<b>DAILY LOG</b>", "Title")
        elements.append(Spacer(1, 12))

        add_paragraph(f"<b>Project:</b> {data.get('project_name', '—')}")
        add_paragraph(f"<b>Client:</b> {data.get('client_name', '—')}")
        add_paragraph(f"<b>Location:</b> {data.get('location', '—')}")
        add_paragraph(f"<b>Date:</b> {data.get('date', '—')}")
        add_paragraph(f"<b>Weather:</b> {data.get('weather', '—')}")
        elements.append(Spacer(1, 12))

        add_paragraph(f"<b>Work Done:</b> {data.get('work_done', '—')}")
        add_paragraph(f"<b>Crew Notes:</b> {data.get('crew_notes', '—')}")
        add_paragraph(f"<b>Safety Notes:</b> {data.get('safety_notes', '—')}")
        elements.append(PageBreak())

        # --- Page 2: Jobsite Photos ---
        if image_paths:
            add_paragraph("<b>📷 Jobsite Photos</b>", "Heading2")
            photo_table = []
            row = []
            for idx, img_path in enumerate(image_paths):
                print(f"🔍 Processing image {idx+1}: {img_path}")
                try:
                    compressed = fix_orientation_and_compress(img_path)
                    img = Image(compressed, width=2.5 * inch, height=2.5 * inch)
                    row.append(img)
                    if len(row) == 2:
                        photo_table.append(row)
                        row = []
                except Exception as e:
                    print(f"⚠️ Error loading image: {e}")
                    continue
            if row:
                photo_table.append(row)
            elements.append(Table(photo_table, hAlign='LEFT'))
            elements.append(PageBreak())
        else:
            print("⚠️ No jobsite images to show on PDF.")

        # --- Page 3: AI Scope Analysis ---
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

                add_paragraph(f"<b>Scope:</b> {scope}<br/><b>Confidence:</b> {conf}%<br/><b>Match:</b> {'✅' if match else '❌'}")
                elements.append(Spacer(1, 6))

                if matched_image:
                    possible_paths = [
                        os.path.join("static/uploads", matched_image),
                        os.path.join("static/uploads", matched_image.replace("_compressed", ""))
                    ]
                    image_found = False
                    for path in possible_paths:
                        if os.path.exists(path):
                            try:
                                img = Image(fix_orientation_and_compress(path), width=2.5*inch, height=2.5*inch)
                                elements.append(img)
                                image_found = True
                                break
                            except Exception as e:
                                print(f"⚠️ Failed to load matched image: {e}")
                    if not image_found:
                        add_paragraph('<font color="red">⚠️ Matched image not found or failed to load.</font>')
                else:
                    add_paragraph('<font color="gray">(No matched image provided)</font>')
                elements.append(Spacer(1, 12))

            out_items = ai_analysis.get("out_of_scope", [])
            if out_items:
                add_paragraph("<b>Out-of-Scope Items:</b>", "Heading3")
                for line in out_items:
                    add_paragraph(f"<font color='red'>• {line}</font>")
            elements.append(PageBreak())

        # --- Page 4: Safety Sheet ---
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            try:
                ext = os.path.splitext(safety_sheet_path)[1].lower()
                if ext in [".jpg", ".jpeg", ".png"]:
                    add_paragraph("📎 Attached Safety Sheet", "Heading2")
                    elements.append(Image(fix_orientation_and_compress(safety_sheet_path), width=5*inch, height=6*inch))
                else:
                    add_paragraph("📎 Attached Safety Sheet: (non-image format, view file separately)", "Heading2")
            except Exception as e:
                print(f"⚠️ Error displaying safety sheet: {e}")
                add_paragraph("⚠️ Error displaying safety sheet.")

        # --- Final Build ---
        print(f"📝 Building PDF: {save_path}")
        doc.build(elements)
        print("✅ PDF successfully generated.")

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        traceback.print_exc()
