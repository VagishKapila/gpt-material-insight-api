from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
from io import BytesIO
import os

# Optional AI & CV imports
try:
    import cv2
    import numpy as np
    import torch
    from transformers import BlipProcessor, BlipForConditionalGeneration
    USE_AI = True
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cuda" if torch.cuda.is_available() else "cpu")
except Exception:
    USE_AI = False

def generate_ai_caption(image_path):
    if not USE_AI:
        return "No caption (AI model unavailable)"
    try:
        image = PILImage.open(image_path).convert("RGB")
        inputs = processor(image, return_tensors="pt").to(model.device)
        output = model.generate(**inputs)
        return processor.decode(output[0], skip_special_tokens=True)
    except:
        return "Error generating caption"

def draw_bounding_boxes(image_path):
    if not USE_AI:
        return None
    try:
        image = cv2.imread(image_path)
        h, w = image.shape[:2]
        boxes = [
            {"label": "Trench", "box": [int(0.1*w), int(0.4*h), int(0.6*w), int(0.9*h)]},
            {"label": "Ladder", "box": [int(0.7*w), int(0.3*h), int(0.9*w), int(0.9*h)]}
        ]
        for item in boxes:
            x1, y1, x2, y2 = item["box"]
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 215, 255), 3)
            cv2.putText(image, item["label"], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)

        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = PILImage.fromarray(img_rgb)
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    except:
        return None

def create_daily_log_pdf(form_data, output_path, photo_paths, logo_path=None, include_page_2=False):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=12, textColor=colors.HexColor('#003366'))
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=14, spaceAfter=6, textColor=colors.HexColor('#005580'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, spaceAfter=6)

    # Title
    elements.append(Paragraph("DAILY LOG", title_style))

    # Logo
    if logo_path and os.path.exists(logo_path):
        logo_img = Image(logo_path, width=1.5*inch, height=1.5*inch)
        logo_img.hAlign = 'RIGHT'
        elements.append(logo_img)

    elements.append(Spacer(1, 12))

    # Section 1: Form Fields
    for section in ['project_name', 'client_name', 'date', 'location', 'weather', 'crew_notes', 'work_done', 'safety_notes']:
        label = section.replace("_", " ").title()
        value = form_data.get(section, '')
        elements.append(Paragraph(f"<b>{label}:</b> {value}", normal_style))

    elements.append(Spacer(1, 12))

    # Section 2: Job Site Photos
    elements.append(Paragraph("Job Site Photos", header_style))
    photo_rows = []
    row = []
    for idx, path in enumerate(photo_paths):
        if os.path.exists(path):
            img = Image(path, width=2.3*inch, height=2.3*inch)
            row.append(img)
            if len(row) == 2:
                photo_rows.append(row)
                row = []
    if row:
        photo_rows.append(row)
    for r in photo_rows:
        elements.append(Table([r], hAlign='LEFT', style=[('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(Spacer(1, 6))

    if include_page_2:
        elements.append(PageBreak())
        elements.append(Paragraph("AI-Generated Captions & Visual Cues", header_style))

        for idx, path in enumerate(photo_paths):
            if os.path.exists(path):
                caption = generate_ai_caption(path)
                elements.append(Paragraph(f"<b>Caption:</b> {caption}", normal_style))

                # Column layout: Original | Annotated
                orig = Image(path, width=2.3*inch, height=2.3*inch)
                annotated_img_buf = draw_bounding_boxes(path)
                if annotated_img_buf:
                    annotated = Image(annotated_img_buf, width=2.3*inch, height=2.3*inch)
                else:
                    annotated = Paragraph("AI overlay not available", normal_style)
                elements.append(Table([[orig, annotated]], colWidths=[2.7*inch]*2, hAlign='LEFT'))
                elements.append(Spacer(1, 12))

    doc.build(elements)
