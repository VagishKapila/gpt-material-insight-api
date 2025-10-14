from flask import Flask, render_template_string, request
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage
import os
import io  # Make sure this was imported

# Load email credentials from environment variables
EMAIL_ADDRESS = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASS')

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<title>Nails & Notes - Daily Log</title>
<h2>Nails & Notes - Daily Log Submission</h2>
<form method=post enctype=multipart/form-data action="/generate-pdf">
  <label>Project ID:</label><br>
  <input type="text" name="project_id" value="proj-001"><br><br>
  <label>Work Summary:</label><br>
  <textarea name="work_summary" rows="4" cols="50">Started grading side yard and removed bricks from backyard.</textarea><br><br>
  <label>Materials Used (comma separated):</label><br>
  <input type="text" name="materials" value="Cement, Steel bar, Sheetrock"><br><br>
  <label>Email to send PDF:</label><br>
  <input type="email" name="email" value=""><br><br>
  <input type="submit" value="Generate PDF">
</form>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        print("✅ [DEBUG] Starting PDF generation...")

        # Extract form fields
        project_id = request.form.get("project_id")
        work_summary = request.form.get("work_summary")
        materials = request.form.get("materials")
        recipient_email = request.form.get("email")

        print("📥 [DEBUG] Form Data:", {
            "project_id": project_id,
            "work_summary": work_summary,
            "materials": materials,
            "email": recipient_email
        })

        # Create PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 800, f"Daily Log - Project: {project_id}")
        c.setFont("Helvetica", 12)
        c.drawString(50, 770, "Work Summary:")
        text = c.beginText(50, 750)
        for line in work_summary.split('\n'):
            text.textLine(line)
        c.drawText(text)

        c.drawString(50, 700, "Materials Used:")
        c.drawString(50, 680, materials)

        c.save()
        pdf_buffer.seek(0)
        print("✅ [DEBUG] PDF created successfully.")

        # Save temporary file
        temp_pdf_path = f"/tmp/{project_id}_DailyLog.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_buffer.read())
        print("💾 [DEBUG] PDF written to", temp_pdf_path)

        # Email the PDF
        msg = EmailMessage()
        msg['Subject'] = f'Daily Log Report - {project_id}'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg.set_content('Attached is your Daily Log PDF.')

        with open(temp_pdf_path, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=f
