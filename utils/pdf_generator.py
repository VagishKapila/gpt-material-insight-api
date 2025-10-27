import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib.units import inch
from PIL import Image as PILImage

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
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # --- Logo ---
    if logo_path and os.path.exists(logo_path):
        try:
            elements.append(Image(logo_path, width=120, height=40))
        except Exception as e:
            print(f"⚠️ Error loading logo image: {e}")
    elements.append(Paragraph("<b>DAILY LOG</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # --- Project Info ---
    elements.append(Paragraph(f"<b>Project:</b> {data.get('project_name', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Date:</b> {data.get('date', '')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Location:</b> {data.get('location', '')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- Weather Icon ---
    if weather_icon_path and os.path.exists(weather_icon_path):
        try:
            elements.append(Image(weather_icon_path, width=40, height=40))
        except Exception as e:
            print(f"⚠️ Weather icon error: {e}")
    elements.append(Spacer(1, 12))

    # --- Work and Safety Notes ---
    for label, key in [("Work Done", "work_done"), ("Safety Notes", "safety_notes")]:
        elements.append(Paragraph(f"<b>{label}:</b>", styles["Heading3"]))
        elements.append(Paragraph(data.get(key, "N/A"), styles["Normal"]))
        elements.append(Spacer(1, 8))

    # --- AI Scope Analysis Page ---
    if ai_analysis:
        elements.append(PageBreak())
        elements.append(Paragraph("<b>AI Scope Analysis</b>", styles["Heading2"]))
        completion = ai_analysis.get("completion", 0)

        try:
            drawing = Drawing(200, 20)
            percent_width = 2 * completion
            drawing.add(Rect(0, 0, 200, 20, fillColor=colors.lightgrey))
            drawing.add(Rect(0, 0, percent_width, 20, fillColor=colors.green))
            elements.append(drawing)
        except Exception as e:
            print(f"⚠️ Drawing error: {e}")
        elements.append(Paragraph(f"<b>Completion:</b> {completion:.1f}%", styles["Normal"]))
        elements.append(Spacer(1, 10))

        scored = ai_analysis.get("scored_items", [])
        if scored:
            table_data = [["Scope Item", "Confidence %", "Match"]]
            for s in scored:
                item = s.get("scope", "N/A")
                confidence = s.get("confidence", 0.0)
                is_match = s.get("match", False)
                table_data.append([
                    item[:75] + ("..." if len(item) > 75 else ""),
                    f"{confidence:.1f}%",
                    "✅" if is_match else "❌"
                ])
            table = Table(table_data, repeatRows=1, colWidths=[300, 80, 40])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(table)

        oos = ai_analysis.get("out_of_scope", [])
        if oos:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("<b>Out-of-Scope Items:</b>", styles["Heading3"]))
            for line in oos:
                elements.append(Paragraph(f"• {line}", styles["Normal"]))

    # --- Job Site Photos Page ---
    if image_paths:
        elements.append(PageBreak())
        elements.append(Paragraph("📸 <b>Job Site Photos</b>", styles["Heading2"]))
        for img_path in image_paths:
            if os.path.exists(img_path):
                try:
                    pil_img = PILImage.open(img_path)
                    pil_img.thumbnail((5*inch, 5*inch))
                    pil_img.save(img_path)  # Overwrite with smaller image
                    elements.append(Image(img_path, width=5*inch, height=pil_img.height / pil_img.width * 5*inch))
                    elements.append(Spacer(1, 8))
                except Exception as e:
                    print(f"⚠️ Error rendering photo: {img_path} — {e}")
                    elements.append(Paragraph(f"⚠️ Failed to load image: {os.path.basename(img_path)}", styles["Normal"]))
            else:
                print(f"❌ Missing photo: {img_path}")
                elements.append(Paragraph(f"❌ Image not found: {os.path.basename(img_path)}", styles["Normal"]))

    # --- Safety Sheet Page ---
    if safety_sheet_path:
        elements.append(PageBreak())
        elements.append(Paragraph("🛡️ <b>Safety Sheet</b>", styles["Heading2"]))
        if os.path.exists(safety_sheet_path):
            try:
                elements.append(Image(safety_sheet_path, width=5*inch, height=6*inch))
            except Exception as e:
                print(f"⚠️ Could not render safety sheet: {e}")
                elements.append(Paragraph(f"⚠️ Failed to display safety sheet image.", styles["Normal"]))
        else:
            print("❌ Safety sheet not found.")
            elements.append(Paragraph("❌ Safety sheet missing.", styles["Normal"]))

    # --- Footer ---
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Confidential – Do Not Duplicate without written consent from BAINS Dev Comm", styles["Normal"]))

    # --- Build PDF ---
    doc.build(elements)
    print(f"✅ PDF successfully created at {save_path}")
