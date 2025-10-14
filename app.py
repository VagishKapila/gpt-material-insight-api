from flask import Flask, request, send_file, render_template_string, jsonify
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import requests
from io import BytesIO
import os

app = Flask(__name__)
styles = getSampleStyleSheet()

# Simulated project metadata
project_db = {
    "proj-001": {
        "project_name": "98 Upper Oaks, San Rafael",
        "location": "98 Upper Oaks, San Rafael",
        "client": "Duncan & Chris Marrs",
        "job_number": "5009",
        "prepared_by": "Vagish Kapila",
        "company_name": "BAINS Dev Comm",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_example.png/600px-Logo_example.png"
    }
}

@app.route("/", methods=["GET"])
def form():
    return render_template_string("""
    <h2>Nails & Notes - Daily Log Submission</h2>
    <form action="/generate-pdf" method="post">
        <label>Project ID: <input type="text" name="project_id" value="proj-001" /></label><br><br>
        <label>Work Summary:<br><textarea name="work_summary" rows="4" cols="60">Started grading side yard and removed bricks from backyard.</textarea></label><br><br>
        <label>Materials Used (comma separated):<br><input type="text" name="materials" value="Cement, Steel bar, Sheetrock" /></label><br><br>
        <input type="submit" value="Generate PDF" />
    </form>
    """)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    data = {
        "project_id": request.form.get("project_id"),
        "work_summary": request.form.get("work_summary", "").split("\n"),
        "materials": [m.strip() for m in request.form.get("materials", "").split(',')]
    }
    project = project_db.get(data["project_id"])
    if not project:
        return "Project not found", 404

    filename = f"/mnt/data/Daily_Log_{data['project_id']}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=LETTER)
    story = []

    logo_url = project.get("logo_url")
    if logo_url:
        try:
            logo_img = ImageReader(requests.get(logo_url, stream=True).raw)
            story.append(Image(logo_img, width=2*inch, height=1*inch))
        except Exception:
            pass

    metadata_table = Table([
        ["Project Name", project["project_name"]],
        ["Location", project["location"]],
        ["Client", project["client"]],
        ["Job #", project["job_number"]],
        ["Prepared By", project["prepared_by"]],
        ["Company", project["company_name"]]
    ], colWidths=[1.8*inch, 4.5*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Work Summary", styles['Heading3']))
    for item in data["work_summary"]:
        story.append(Paragraph(f"• {item}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Materials Used", styles['Heading3']))
    for material in data["materials"]:
        story.append(Paragraph(f"• {material}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(PageBreak())
    story.append(Paragraph("Photographs / Attachments", styles['Heading2']))
    story.append(Paragraph("(* Photos would appear here in full system *)", styles["Italic"]))
    story.append(PageBreak())

    story.append(Paragraph("Material Comparison & Recommendations (AI-Generated)", styles['Heading2']))
    story.append(Paragraph("Detected Material: Sheetrock", styles["Normal"]))
    story.append(Paragraph("Cheapest Option: Lowe’s – $8.35", styles["Normal"]))
    story.append(Paragraph("Alternatives: Fiber Cement Board – Water/Fire resistant ($9–$12)", styles["Normal"]))
    story.append(Paragraph("Recommendation: Use Sheetrock for interiors. Fiber cement for wet zones.", styles["Normal"]))

    doc.build(story)
    return send_file(filename, as_attachment=True)

@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    content = request.json
    image_url = content.get("image_url")
    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400

    return jsonify({
        "material": "Sheetrock",
        "cheapest_found": {
            "supplier": "Lowe’s",
            "price": "$8.35",
            "location": "San Jose, CA",
            "url": "https://www.lowes.com"
        },
        "alternatives": [
            {
                "name": "Fiber Cement Board",
                "benefits": ["Water resistant", "Fire retardant"],
                "price_range": "$9 - $12"
            }
        ],
        "recommendation": "Use drywall for interior, fiber cement for moisture-prone zones.",
        "message": "Standard drywall is suitable for most interior applications."
    })

if __name__ == "__main__":
    app.run(debug=True)