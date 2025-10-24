from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PyPDF2 import PdfMerger
from PIL import Image as PILImage
import os

def create_daily_log_pdf(data, image_paths, output_path, logo_path=None, ai_analysis=None, progress_report=None, safety_path=None):
    temp_output_path = "temp_output.pdf"

    doc = SimpleDocTemplate(temp_output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # ----------------------------
    # Styles
    # ----------------------------
    header_style = ParagraphStyle(name='HeaderStyle', fontSize=16, leading=20, spaceAfter=12, alignment=1)
    subheader_style = ParagraphStyle(name='SubHeaderStyle', fontSize=12, leading=15, spaceAfter=10)
    footer_style = ParagraphStyle(name='FooterStyle', fontSize=8, alignment=1, spaceBefore=12)

    # ----------------------------
    # Title Page
    # ----------------------------
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2.5 * inch, height=2.5 * inch)
            logo.hAlign = 'CENTER'
            elements.append(logo)
        except Exception as e:
            print(f"[⚠️] Logo error: {e}")

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("DAILY LOG", header_style))
    elements.append(Spacer(1, 0.1 * inch))

    for key, value in data.items():
        elements.append(Paragraph(f"<b>{key}:</b> {value}", subheader_style))
    elements.append(PageBreak())

    # ----------------------------
    # Jobsite Photos Page
    # ----------------------------
    if image_paths:
        elements.append(Paragraph("Jobsite Photos", header_style))
        elements.append(Spacer(1, 0.2 * inch))

        for i, img_path in enumerate(image_paths):
            try:
                if not os.path.exists(img_path):
                    print(f"[❌] File not found: {img_path}")
                    continue

                file_size = os.path.getsize(img_path)
                print(f"[📁] {img_path} size: {file_size} bytes")

                # Verify image integrity
                try:
                    img_check = PILImage.open(img_path)
                    img_check.verify()
                except Exception as e:
                    print(f"[❌] Corrupt or unreadable image: {img_path} — {e}")
                    continue  # Skip bad image

                # Reopen and process
                pil_img = PILImage.open(img_path)
                width, height = pil_img.size

                # Rotate if landscape
                if width > height:
                    pil_img = pil_img.rotate(90, expand=True)

                # Resize to max width of 1600px
                if pil_img.width > 1600:
                    ratio = 1600 / pil_img.width
                    new_height = int(pil_img.height * ratio)
                    pil_img = pil_img.resize((1600, new_height), PILImage.Resampling.LANCZOS)
                    print(f"[🖼️] Resized {img_path} to width 1600px, height {new_height}px")

                # Save processed image
                pil_img.save(img_path)

                # Add to PDF
                img = Image(img_path, width=3.2 * inch, height=2.4 * inch)
                img.hAlign = 'CENTER'
                elements.append(img)

                if i % 2 == 1:
                    elements.append(PageBreak())
                else:
                    elements.append(Spacer(1, 0.2 * inch))

            except Exception as e:
                print(f"[❌] Error loading image {img_path}: {e}")
                continue

    # ----------------------------
    # AI/AR Analysis Page
    # ----------------------------
    if ai_analysis:
        elements.append(PageBreak())
        elements.append(Paragraph("AI/AR Analysis", header_style))
        ai_formatted = ai_analysis.replace('\n', '<br/>')
        elements.append(Paragraph(f"<b>Image Insights:</b><br/>{ai_formatted}", subheader_style))

    # ----------------------------
    # Scope Progress Page
    # ----------------------------
    if progress_report:
        elements.append(PageBreak())
        elements.append(Paragraph("Scope Progress Tracker", header_style))
        progress_formatted = progress_report.replace('\n', '<br/>')
        elements.append(Paragraph(f"<b>Progress Summary:</b><br/>{progress_formatted}", subheader_style))

    # ----------------------------
    # Footer
    # ----------------------------
    elements.append(PageBreak())
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph("Confidential – Do Not Duplicate without written consent from BAINS Dev Comm", footer_style))

    # Build primary PDF
    try:
        doc.build(elements)
        print("[✅] Main PDF built successfully.")
    except Exception as e:
        print(f"[❌] Error building main PDF: {e}")
        return

    # ----------------------------
    # Merge with Safety Sheet (if provided)
    # ----------------------------
    if safety_path and os.path.exists(safety_path):
        try:
            file_size = os.path.getsize(safety_path)
            print(f"[📁] Safety sheet size: {file_size} bytes")

            # Verify safety sheet
            try:
                sheet_check = PILImage.open(safety_path)
                sheet_check.verify()
                print("[🧾] Safety sheet passed integrity check.")
            except Exception as e:
                print(f"[❌] Safety sheet corrupt or unreadable: {safety_path} — {e}")
                os.rename(temp_output_path, output_path)
                return

            merger = PdfMerger()
            merger.append(temp_output_path)
            merger.append(safety_path)
            merger.write(output_path)
            merger.close()
            os.remove(temp_output_path)
            print("[✅] Merged safety sheet successfully.")

        except Exception as e:
            print(f"[❌] Error merging safety sheet: {e}")
            os.rename(temp_output_path, output_path)
    else:
        os.rename(temp_output_path, output_path)
        print("[ℹ️] No safety sheet provided, finalized single PDF.")
