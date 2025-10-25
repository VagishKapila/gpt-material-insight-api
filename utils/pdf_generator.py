import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage

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
    print("🚀 Starting PDF generation")
    print(f"→ ai_analysis={ai_analysis}, has progress_report={bool(progress_report)}")

    doc = SimpleDocTemplate(save_path, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SectionTitle", fontSize=14, leading=16, spaceAfter=8, textColor=colors.HexColor("#003366")))
    styles.add(ParagraphStyle(name="Body", fontSize=11, leading=14))

    elements = []

    # === Page 1 ===
    print("📄 Page 1: Daily metadata")
    elements.append(Paragraph("DAILY LOG", styles["Title"]))
    elements.append(Spacer(1, 8))
    if logo_path and os.path.exists(logo_path):
        elements.append(Image(logo_path, width=1.8*inch, height=0.8*inch))
        elements.append(Spacer(1, 8))
    for field in ["project_name", "client_name", "location", "date", "weather"]:
        if field in data:
            elements.append(Paragraph(f"<b>{field.title()}:</b> {data[field]}", styles["Body"]))
            elements.append(Spacer(1, 4))
    for section in ["crew_notes", "work_done", "safety_notes"]:
        if section in data and data[section].strip():
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(section.replace("_", " ").title(), styles["SectionTitle"]))
            elements.append(Paragraph(data[section], styles["Body"]))
    elements.append(PageBreak())

    # === Page 2 ===
    print("📸 Page 2: Photos")
    elements.append(Paragraph("JOB SITE PHOTOS", styles["SectionTitle"]))
    if not image_paths:
        elements.append(Paragraph("No job site photos uploaded.", styles["Body"]))
    for path in image_paths:
        try:
            img = PILImage.open(path).convert("RGB")  # ✅ fix RGBA bug
            temp_jpg = f"{path}_rgb.jpg"
            img.save(temp_jpg, "JPEG")
            elements.append(Image(temp_jpg, width=5.5*inch, height=3.5*inch))
            elements.append(Spacer(1, 10))
        except Exception as e:
            print(f"⚠️ Image load error: {e}")
            elements.append(Paragraph(f"Error loading {os.path.basename(path)}: {e}", styles["Body"]))
    elements.append(PageBreak())

    # === Page 3 ===
    print("🤖 Page 3: AI / Scope Analysis")
    elements.append(Paragraph("AI / SCOPE ANALYSIS", styles["SectionTitle"]))
    if progress_report:
        matched = progress_report.get("matched", [])
        missing = progress_report.get("flagged_missing", [])
        out_scope = progress_report.get("out_of_scope", [])
        percent = progress_report.get("percent_complete", 0)

        # Summary table
        data_table = [
            ["Matched", len(matched)],
            ["Missing", len(missing)],
            ["Out of Scope", len(out_scope)],
            ["Completion", f"{percent}%"]
        ]
        t = Table(data_table, colWidths=[2.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        if matched:
            elements.append(Paragraph("✅ Matched Items:", styles["Body"]))
            for m in matched:
                elements.append(Paragraph(f"• {m}", styles["Body"]))
        if missing:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("❌ Missing Items:", styles["Body"]))
            for m in missing:
                elements.append(Paragraph(f"• {m}", styles["Body"]))
        if out_scope:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("🚫 Out of Scope:", styles["Body"]))
            for o in out_scope:
                elements.append(Paragraph(f"• {o}", styles["Body"]))
    else:
        print("❌ No progress report received")
        elements.append(Paragraph("⚠️ No AI/Scope analysis data found.", styles["Body"]))
    elements.append(PageBreak())

    # === Page 4 ===
    print("📋 Page 4: Safety Sheet")
    if safety_sheet_path and os.path.exists(safety_sheet_path):
        try:
            img = PILImage.open(safety_sheet_path).convert("RGB")
            temp_jpg = f"{safety_sheet_path}_rgb.jpg"
            img.save(temp_jpg, "JPEG")
            elements.append(Image(temp_jpg, width=5.8*inch, height=8.5*inch))
        except Exception as e:
            print(f"⚠️ Safety sheet error: {e}")
            elements.append(Paragraph("Error loading safety sheet.", styles["Body"]))
    else:
        elements.append(Paragraph("No safety sheet uploaded.", styles["Body"]))

    # === Build ===
    try:
        print("🛠 Building PDF…")
        doc.build(elements)
        print(f"✅ PDF created at {save_path}")
    except Exception as e:
        print(f"❌ PDF build failed: {e}")
