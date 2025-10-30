import os
from PIL import Image as PILImage, ExifTags
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def fix_orientation(image_path):
    """Auto-rotate and compress image for PDF embedding"""
    try:
        img = PILImage.open(image_path)
        # Fix rotation based on EXIF data
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif = img._getexif()
        if exif and orientation in exif:
            if exif[orientation] == 3:
                img = img.rotate(180, expand=True)
            elif exif[orientation] == 6:
                img = img.rotate(270, expand=True)
            elif exif[orientation] == 8:
                img = img.rotate(90, expand=True)
        img.thumbnail((800, 800))
        temp_path = image_path.replace(".jpg", "_fixed.jpg").replace(".png", "_fixed.png")
        img.save(temp_path, quality=70)
        return temp_path
    except Exception:
        return image_path

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
    try:
        doc = SimpleDocTemplate(save_path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def add_footer(canvas, doc):
            footer_text = "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm"
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.drawString(inch, 0.5 * inch, footer_text)
            canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {doc.page}")
            canvas.restoreState()

        # --- Page 1: Log Info ---
        if logo_path and os.path.exists(logo_path):
            elements.append(Image(logo_path, width=120, height=60))
        elements.append(Paragraph("<b>Daily Construction Log</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

        info_table = [
            ["Project Name:", data.get("project_name", "")],
            ["Client Name:", data.get("client_name", "")],
            ["Location:", data.get("location", "")],
            ["Date:", data.get("date", "")],
            ["Weather:", data.get("weather", "")],
        ]
        t = Table(info_table, colWidths=[120, 380])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        work_notes = [
            ["Work Performed", data.get("work_done", "")],
            ["Crew Notes", data.get("crew_notes", "")],
            ["Safety Notes", data.get("safety_notes", "")]
        ]
        elements.append(Table(work_notes, colWidths=[120, 380],
                              style=[('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
        elements.append(PageBreak())

        # --- Page 2: Photos ---
        elements.append(Paragraph("<b>📸 Jobsite Photos</b>", styles["Heading2"]))
        photo_row = []
        count = 0

        for img_path in image_paths:
            if not os.path.exists(img_path):
                continue
            fixed = fix_orientation(img_path)
            try:
                photo = Image(fixed, width=2.7 * inch, height=2 * inch)
                photo_row.append(photo)
                count += 1
                if count % 2 == 0:
                    elements.append(Table([photo_row], colWidths=[3*inch, 3*inch]))
                    elements.append(Spacer(1, 8))
                    photo_row = []
            except Exception:
                continue

        if photo_row:
            elements.append(Table([photo_row], colWidths=[3*inch] * len(photo_row)))
        elements.append(PageBreak())

        # --- Page 3: AI Analysis ---
        if ai_analysis:
            elements.append(Paragraph("<b>🤖 AI Scope Analysis</b>", styles["Heading2"]))
            elements.append(Spacer(1, 8))

            completion = ai_analysis.get("completion", 0)
            elements.append(Paragraph(f"<b>Overall Estimated Completion:</b> {completion:.1f}%", styles["Normal"]))
            elements.append(Spacer(1, 6))

            scored_items = ai_analysis.get("scored_items", [])
            if scored_items:
                data_table = [["Scope Item", "Match", "Confidence", "Matched Image"]]
                for item in scored_items:
                    match_status = "✅" if item.get("match") else "❌"
                    confidence = f"{item.get('confidence', 0)}%"
                    matched_image = os.path.basename(item.get("matched_image", "") or "")
                    data_table.append([
                        item.get("scope", "—"),
                        match_status,
                        confidence,
                        matched_image or "—"
                    ])

                table = Table(data_table, colWidths=[220, 60, 80, 140])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER')
                ]))
                elements.append(table)
            else:
                elements.append(Paragraph("⚠️ No AI analysis results available.", styles["Normal"]))
            elements.append(PageBreak())

        # --- Page 4: Safety Sheet ---
        if safety_sheet_path and os.path.exists(safety_sheet_path):
            elements.append(Paragraph("<b>🦺 Safety Sheet</b>", styles["Heading2"]))
            elements.append(Spacer(1, 12))
            try:
                if safety_sheet_path.lower().endswith((".jpg", ".jpeg", ".png")):
                    fixed = fix_orientation(safety_sheet_path)
                    elements.append(Image(fixed, width=6*inch, height=7*inch))
                else:
                    elements.append(Paragraph("Safety sheet attached separately.", styles["Normal"]))
            except Exception:
                elements.append(Paragraph("⚠️ Unable to display safety sheet.", styles["Normal"]))

        # --- Build PDF ---
        doc.build(elements, onLaterPages=add_footer, onFirstPage=add_footer)

    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
