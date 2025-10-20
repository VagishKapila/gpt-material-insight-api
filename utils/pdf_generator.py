from PIL import Image, ImageDraw, ImageFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from utils.image_analyzer import analyze_and_overlay

def analyze_and_overlay(image_path, output_path):
    """Analyze image, overlay a caption and bounding box, and save to output_path."""
    image = Image.open(image_path).convert("RGB")

    # Generate caption
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    # Draw bounding box and caption
    draw = ImageDraw.Draw(image)
    width, height = image.size
    box_width, box_height = width // 2, height // 3
    left = (width - box_width) // 2
    top = (height - box_height) // 2
    right = left + box_width
    bottom = top + box_height
    draw.rectangle([left, top, right, bottom], outline="red", width=4)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    text_position = (left, max(top - 30, 10))
    draw.text(text_position, caption, fill="red", font=font)

    image.save(output_path)
    return output_path, caption

def create_daily_log_pdf(form_data, output_path, photo_paths, logo_path=None, include_page_2=True):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=12, textColor=colors.HexColor('#003366'))
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=14, spaceAfter=6, textColor=colors.HexColor('#005580'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, spaceAfter=6)

    # Add logo if provided
    if logo_path and os.path.exists(logo_path):
        elements.append(RLImage(logo_path, width=100, height=50))
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("DAILY LOG", title_style))
    for key, value in form_data.items():
        elements.append(Paragraph(f"<b>{key}:</b> {value}", normal_style))

    if include_page_2:
        elements.append(PageBreak())
        elements.append(Paragraph("Site Photos with Captions", header_style))
        for photo_path in photo_paths:
            captioned_path, caption = analyze_and_overlay(photo_path, photo_path)
            elements.append(RLImage(captioned_path, width=400, height=300))
            elements.append(Paragraph(f"<i>{caption}</i>", normal_style))
            elements.append(Spacer(1, 12))

    doc.build(elements)
    return output_path
