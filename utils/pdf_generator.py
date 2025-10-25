import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle

from PyPDF2 import PdfMerger

def create_daily_log_pdf(
    data,
    image_paths,
    logo_path,
    ai_analysis,
    progress_report,
    save_path,
    weather_icon_path,
    safety_sheet_path
):
    print("✅ Starting PDF generation...")

    try:
        doc = SimpleDocTemplate(save_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Header (Page 1)
        print("📄 Adding Page 1 - Project Metadata and Daily Notes")
        elements.append(Paragraph("DAILY LOG", styles["Title"]))
        elements.append(Spacer(1, 12))

        for key, value in data.items():
            elements.append(Paragraph(f"<b>{key}:</b> {value}", styles["Normal"]))
        elements.append(PageBreak())

        # Photos (Page 2)
        print("📸 Adding Page 2 - Job Site Photos")
        if image_paths:
            for img_path in image_paths:
                if os.path.exists(img_path):
                    try:
                        im = Image(img_path, width=4*inch, height=3*inch)
                        elements.append(im)
                        elements.append(Spacer(1, 12))
                    except Exception as e:
                        print(f"⚠️ Image error: {e}")
        else:
            elements.append(Paragraph("No job site photos uploaded.", styles["BodyText"]))
        elements.append(PageBreak())

        # AI Analysis (Page 3)
        print("🤖 Adding Page 3 - AI/Scope Analysis")
        elements.append(Paragraph("AI Scope Comparison", styles["Heading2"]))
        if progress_report:
            matched = progress_report.get("matched", [])
            unmatched = progress_report.get("unmatched", [])
            summary = progress_report.get("summary", "No summary found.")

            if matched:
                elements.append(Paragraph("✅ Matched Items:", styles["BodyText"]))
                for item in matched:
                    elements.append(Paragraph(f"• {item}", styles["Normal"]))
            else:
                elements.append(Paragraph("No matched items.", styles["BodyText"]))

            if unmatched:
                elements.append(Spacer(1, 6))
                elements.append(Paragraph("❌ Unmatched Items:", styles["BodyText"]))
                for item in unmatched:
                    elements.append(Paragraph(f"• {item}", styles["Normal"]))
            else:
                elements.append(Paragraph("No unmatched items.", styles["BodyText"]))

            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"<b>Summary:</b> {summary}", styles["BodyText"]))
        else:
            print("❌ No progress report data received!")
            elements.append(Paragraph("⚠️ No scope analysis data available.", styles["BodyText"]))

        elements.append(PageBreak())

        # Safety Sheet (Page 4)
        print("📋 Adding Page 4 - Safety Sheet")
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            try:
                safety_img = Image(safety_sheet_path, width=5.5*inch, height=7*inch)
                elements.append(safety_img)
            except Exception as e:
                print(f"⚠️ Safety sheet image error: {e}")
                elements.append(Paragraph("Error rendering safety sheet.", styles["BodyText"]))
        else:
            elements.append(Paragraph("No safety sheet uploaded.", styles["BodyText"]))

        print("🛠 Building PDF...")
        doc.build(elements)
        print("✅ PDF built successfully!")

    except Exception as e:
        print(f"❌ Failed to build PDF: {e}")
