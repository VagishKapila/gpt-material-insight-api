import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image as PILImage
import time

def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report, save_path, weather_icon_path, safety_sheet_path=None):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    story = []

    # Logo
    if logo_path and os.path.exists(logo_path):
        story.append(Image(logo_path, width=100, height=50))
        story.append(Spacer(1, 12))

    # Title
    story.append(Paragraph("DAILY LOG", styles['Title']))
    story.append(Spacer(1, 12))

    # Metadata
    for key in ['project_name', 'location', 'date', 'crew_notes', 'work_done', 'safety_notes', 'weather']:
        value = data.get(key, '')
        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
        story.append(Spacer(1, 6))

    # Weather icon
    if weather_icon_path and os.path.exists(weather_icon_path):
        story.append(Image(weather_icon_path, width=50, height=50))
        story.append(Spacer(1, 12))

    story.append(PageBreak())

    # Page 2: Photos (2-column)
    for idx, path in enumerate(image_paths):
        if os.path.exists(path):
            story.append(Paragraph(f"Job Site Photo {idx+1}", styles['Heading4']))
            story.append(Image(path, width=250, height=180))
            story.append(Spacer(1, 12))

    story.append(PageBreak())

    # Page 3: AI Analysis
    story.append(Paragraph("AI Analysis and Material Insight", styles['Heading2']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(ai_analysis or "No AI analysis available.", styles['Normal']))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Scope Progress Status", styles['Heading2']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(progress_report or "No progress report available.", styles['Normal']))
    story.append(PageBreak())

    # Save the initial PDF
    doc.build(story)

    # Page 4: Safety Sheet Merge (if provided)
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        print(f"[🧾] Attempting to merge safety sheet: {safety_sheet_path}")
        try:
            merger = PdfMerger()
            merger.append(PdfReader(save_path, strict=False))

            # Check file type — only merge if it's a PDF
            ext = os.path.splitext(safety_sheet_path)[-1].lower()
            if ext == ".pdf":
                merger.append(PdfReader(safety_sheet_path, strict=False))
            else:
                raise ValueError("Safety sheet is not a PDF, converting to PDF...")

            merger.write(save_path)
            merger.close()
            print(f"[✅] Safety sheet merged into final PDF.")
        except Exception as e:
            print(f"[❌] Error merging safety sheet: {e}")
            try:
                # Fallback: Convert image to PDF and re-merge
                image = PILImage.open(safety_sheet_path)
                fallback_pdf = safety_sheet_path.rsplit(".", 1)[0] + "_fallback.pdf"
                image.convert("RGB").save(fallback_pdf)
                merger = PdfMerger()
                merger.append(PdfReader(save_path, strict=False))
                merger.append(PdfReader(fallback_pdf, strict=False))
                merger.write(save_path)
                merger.close()
                print(f"[🛠️] Fallback safety sheet added as page.")
            except Exception as e2:
                print(f"[❌] Fallback merge failed: {e2}")

    # Delay (Best Practice)
    time.sleep(1)
    print(f"✅ PDF generated: {save_path}")
