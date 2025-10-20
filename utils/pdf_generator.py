import os
import replicate
from PIL import Image, ImageDraw, ImageFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# Make sure your REPLICATE_API_TOKEN is set in Render environment
replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

def analyze_and_overlay(image_path):
    """
    Uses Replicate to generate a caption for an image,
    then overlays that caption and a visual bounding box.
    """
    caption = "No caption generated"
    try:
        output = replicate.run(
            "methexis-inc/img2prompt:latest",
            input={"image": open(image_path, "rb")}
        )
        caption = output.strip() if isinstance(output, str) else "AI caption unavailable"
    except Exception as e:
        caption = f"AI caption error: {e}"

    # Open image for drawing
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Draw a bounding box
    box_color = (255, 0, 0)
    margin = int(min(width, height) * 0.05)
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=box_color,
        width=4
    )

    # Draw caption text
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    text_x, text_y = margin + 10, margin + 10
    draw.text((text_x, text_y), caption, fill=box_color, font=font)

    # Save annotated image
    output_path = image_path.replace(".jpg", "_captioned.jpg")
    image.save(output_path)
    return caption, output_path


def create_daily_log_pdf(form_data, output_path, photo_paths, logo_path=None, include_page_2=True):
    """
    Create a formatted daily log PDF with optional AI captions.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                 alignment=1, fontSize=18, spaceAfter=12,
                                 textColor=colors.HexColor('#003366'))
    header_style = ParagraphStyle('Header', parent=styles['Heading2'],
                                  fontSize=14, spaceAfter=6,
                                  textColor=colors.HexColor('#005580'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
                                  fontSize=11, spaceAfter=6)

    # Add logo
    if logo_path and os.path.exists(logo_path):
        elements.append(RLImage(logo_path, width=100, height=50))
        elements.append(Spacer(1, 12))

    # Title
    elements.append(Paragraph("DAILY LOG REPORT", title_style))
    for key, value in form_data.items():
        elements.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", normal_style))

    # Add jobsite photos + AI captions
    if include_page_2 and photo_paths:
        elements.append(PageBreak())
        elements.append(Paragraph("Site Photos with AI Captions", header_style))

        for photo_path in photo_paths:
            try:
                caption, captioned_image = analyze_and_overlay(photo_path)
                elements.append(RLImage(captioned_image, width=400, height=300))
                elements.append(Paragraph(f"<i>{caption}</i>", normal_style))
                elements.append(Spacer(1, 12))
            except Exception as e:
                elements.append(Paragraph(f"Error processing {photo_path}: {e}", normal_style))

    doc.build(elements)
    return output_path
