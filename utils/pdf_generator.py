import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from PIL import Image as PILImage
from io import BytesIO

# Try to import OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

def create_daily_log_pdf(form_data, output_path, photo_paths, logo_path=None, include_page_2=False):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=12, textColor=colors.HexColor('#003366'))
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=14, spaceAfter=6, textColor=colors.HexColor('#005580'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, spaceAfter=6)

    from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import cv2
import numpy as np
import torch

# Load AI Captioning Model once (if GPU/CPU available)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cuda" if torch.cuda.is_available() else "cpu")

def generate_ai_caption(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(image, return_tensors="pt").to(model.device)
    output = model.generate(**inputs)
    return processor.decode(output[0], skip_special_tokens=True)

def detect_safety_gear(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return []
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    orange_mask = cv2.inRange(hsv, (5,100,100), (15,255,255))   # Safety vest
    yellow_mask = cv2.inRange(hsv, (25,100,100), (35,255,255)) # Helmet

    tags = []
    if np.sum(orange_mask) > 10000:
        tags.append("Safety vest detected")
    if np.sum(yellow_mask) > 10000:
        tags.append("Helmet detected")
    if not tags:
        tags.append("No visible safety gear detected")
    return tags

def add_ai_captions_page(story, photo_paths, styles):
    from reportlab.platypus import Image as RLImage, Spacer, Paragraph
    from reportlab.lib.units import inch

    story.append(Paragraph("Page 2: AI-Powered Photo Insights", styles['Heading1']))
    story.append(Spacer(1, 12))

    for path in photo_paths:
        try:
            caption = generate_ai_caption(path)
            tags = detect_safety_gear(path)

            story.append(RLImage(path, width=3.5*inch, height=3.5*inch))
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>AI Caption:</b> {caption}", styles['Normal']))
            story.append(Paragraph(f"<b>Visual Tags:</b> {', '.join(tags)}", styles['Normal']))
            story.append(Spacer(1, 18))
        except Exception as e:
            story.append(Paragraph(f"Error analyzing image {path}: {e}", styles['Normal']))
            

    # --- Logo at the top ---
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=2.2 * inch, height=1 * inch))
        elements.append(Spacer(1, 0.2 * inch))

    # --- Title ---
    elements.append(Paragraph("DAILY LOG REPORT", title_style))
    elements.append(Spacer(1, 0.15 * inch))

    # --- Form Data Section (Two columns layout) ---
    field_names = {
        "project_name": "Project Name",
        "project_address": "Project Address",
        "weather": "Weather",
        "date": "Date",
        "crew_notes": "Crew Notes",
        "work_done": "Work Done",
        "safety_notes": "Safety Notes",
        "material_summary": "Material Summary",
        "equipment_used": "Equipment Used",
        "hours_worked": "Hours Worked",
    }

    left_column = []
    right_column = []

    for i, (key, label) in enumerate(field_names.items()):
        value = form_data.get(key, "")
        para = Paragraph(f"<b>{label}:</b> {value}", normal_style)
        if i % 2 == 0:
            left_column.append(para)
        else:
            right_column.append(para)

    max_len = max(len(left_column), len(right_column))
    while len(left_column) < max_len:
        left_column.append(Paragraph("", normal_style))
    while len(right_column) < max_len:
        right_column.append(Paragraph("", normal_style))

    table_data = list(zip(left_column, right_column))
    table = Table(table_data, colWidths=[3.8 * inch, 3.8 * inch])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))

    # --- Footer ---
    elements.append(Spacer(1, 0.5 * inch))
    footer = Paragraph('<para alignment="center"><font size=10 color="#888888">Powered by Nails & Notes</font></para>', normal_style)
    elements.append(footer)

    # --- Page 2: Raw Uploaded Images ---
    if photo_paths:
        elements.append(PageBreak())
        elements.append(Paragraph("Uploaded Job Site Photos", header_style))
        img_table = []
        row = []

        for i, path in enumerate(photo_paths):
            img = compress_image_for_report(path)
            row.append(img)
            if (i + 1) % 2 == 0:
                img_table.append(row)
                row = []

        if row:
            img_table.append(row)

        for r in img_table:
            elements.append(Table([r], colWidths=[3.8 * inch] * len(r), hAlign='LEFT'))
            elements.append(Spacer(1, 0.2 * inch))

    # --- Page 3: AR Overlay using OpenCV ---
    if include_page_2 and OPENCV_AVAILABLE and photo_paths:
        elements.append(PageBreak())
        elements.append(Paragraph("AR Analysis & Image Highlights", header_style))

        overlay_rows = []
        row = []
        for i, path in enumerate(photo_paths[:6]):
            img_io = apply_opencv_overlay(path)
            img = Image(img_io, width=3.6 * inch, height=2.2 * inch)
            row.append(img)
            if (i + 1) % 2 == 0:
                overlay_rows.append(row)
                row = []

        if row:
            overlay_rows.append(row)

        for r in overlay_rows:
            elements.append(Table([r], colWidths=[3.8 * inch] * len(r), hAlign='LEFT'))
            elements.append(Spacer(1, 0.2 * inch))
    elif include_page_2 and not OPENCV_AVAILABLE:
        elements.append(PageBreak())
        elements.append(Paragraph("⚠️ OpenCV not installed — AR page skipped", normal_style))

    # Build PDF
    doc.build(elements)


def compress_image_for_report(image_path, max_width=400):
    try:
        img = PILImage.open(image_path)
        img.thumbnail((max_width, max_width * 1.5))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return Image(buffer, width=img.width * 0.75, height=img.height * 0.75)
    except Exception as e:
        print(f"Error compressing image: {e}")
        return Paragraph("⚠️ Error loading image", getSampleStyleSheet()["Normal"])


def apply_opencv_overlay(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image.")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        _, buffer = cv2.imencode(".png", edges_colored)
        io_buf = BytesIO(buffer)
        io_buf.seek(0)
        return io_buf
    except Exception as e:
        print(f"OpenCV error: {e}")
        return BytesIO()
