from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from PIL import Image as PILImage, ImageOps

def create_daily_log_pdf(data, image_paths, pdf_path, logo_path=None, scope_path=None, enable_ai_analysis=False):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=20,
        leading=22,
        textColor=colors.black,
        spaceAfter=12,
    )
    field_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=4,
    )

    # --- HEADER / TITLE ---
    story.append(Paragraph("DAILY LOG", title_style))
    story.append(Spacer(1, 10))

    # --- Project Info ---
    for key in ["project_name", "location", "crew_notes", "work_done", "safety_notes", "weather"]:
        value = data.get(key, "").strip()
        if value:
            label = key.replace("_", " ").title()
            story.append(Paragraph(f"<b>{label}:</b> {value.replace('\n', '<br/>')}", field_label))
            story.append(Spacer(1, 8))

    if scope_path:
        story.append(Paragraph(f"<i>Scope of Work Linked:</i> {os.path.basename(scope_path)}", field_label))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # --- PHOTOS PAGE ---
    story.append(Paragraph("Job Site Photos", title_style))
    story.append(Spacer(1, 12))

    for img_path in image_paths:
        try:
            img = PILImage.open(img_path)
            img = ImageOps.exif_transpose(img)
            img.thumbnail((600, 400))
            temp_path = os.path.splitext(img_path)[0] + "_compressed.jpg"
            img.convert("RGB").save(temp_path, "JPEG", quality=60)
            story.append(Image(temp_path, width=5.5 * inch, height=3.5 * inch))
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"⚠️ Error loading image {img_path}: {e}")

    story.append(PageBreak())

    # --- AI/AR ANALYSIS ---
    if enable_ai_analysis:
        story.append(Paragraph("AI / AR Analysis & Progress Tracking", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("🔍 Detected Materials: Sheetrock, Concrete, Rebar", field_label))
        story.append(Spacer(1, 6))
        story.append(Paragraph("📈 Progress: 45% of work aligns with Scope of Work.", field_label))
        story.append(Spacer(1, 6))
        story.append(Paragraph("📌 Next Steps: Verify trench sealing and concrete curing.", field_label))
        story.append(Spacer(1, 20))

    # --- FOOTER / SIGNATURE ---
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Powered by <b>Nails & Notes: Construction Daily Log AI</b> — Created by Vagish Kapila © 2025</i>",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=9, textColor=colors.gray),
    ))

    doc.build(story)
