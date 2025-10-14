
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
import io
import os

app = Flask(__name__)

UPLOAD_FOLDER = "generated_pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    project_id = request.form.get("project_id", "Unknown")
    work_summary = request.form.get("work_summary", "N/A")
    materials = request.form.get("materials", "N/A")

    # Generate PDF in memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, f"Project ID: {project_id}")
    c.drawString(100, 730, f"Work Summary: {work_summary}")
    c.drawString(100, 710, f"Materials Used: {materials}")
    c.save()
    buffer.seek(0)

    # Save PDF locally
    file_path = os.path.join(UPLOAD_FOLDER, f"{project_id}_DailyLog.pdf")
    with open(file_path, "wb") as f:
        f.write(buffer.read())

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{project_id}_DailyLog.pdf",
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    app.run(debug=True)
