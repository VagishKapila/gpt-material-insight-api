from flask import Flask, render_template, request
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage
import os
import io

app = Flask(__name__)

# Load environment variables
EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASS")

@app.route("/")
def index():
    return "<h1>Nails & Notes: Daily Log API is Running!</h1>"

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        print("✅ [DEBUG] Starting PDF generation...")

        # Get form data
        project_id = request.form.get("project_id", "unknown")
        work_summary = request.form.get("work_summary", "N/A")
        materials = request.form.get("materials", "N/A")
        recipient_email = request.form.get("email", EMAIL_ADDRESS)

        print("📥 [DEBUG] Form Data:", {
            "project_id": project_id,
            "work_summary": work_summary,
            "materials": materials,
            "email": recipient_email
        })

        # Generate PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, f"Project ID: {project_id}")
        c.drawString(100, 730, f"Work Summary: {work_summary}")
        c.drawString(100, 710, f"Materials Used: {materials}")
        c.save()

        buffer.seek(0)
        print("✅ [DEBUG] PDF created successfully.")

        # Save to temporary file (for email attachment)
        temp_pdf_path = f"/tmp/{project_id}_DailyLog.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(buffer.read())
        print("💾 [DEBUG] PDF written to", temp_pdf_path)

        # Send Email
        msg = EmailMessage()
        msg['Subject'] = f'Daily Log Report - {project_id}'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg.set_content('Attached is your Daily Log PDF.')

        with open(temp_pdf_path, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=f"{project_id}_DailyLog.pdf")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("📧 [DEBUG] Email sent successfully to:", recipient_email)
        return "✅ Daily Log PDF created and emailed!"

    except Exception as e:
        print("❌ [ERROR] Exception occurred:", str(e))
        return f"❌ Internal Server Error: {str(e)}", 500

@app.route("/generate-pdf-dummy")
def test_generate_pdf():
    print("✅ [DEBUG] Starting PDF generation test...")

    try:
        # Dummy test values
        project_id = "test-project"
        work_summary = "This is a test PDF generated for debugging purposes."
        materials = "Bricks, Cement, Steel"
        recipient_email = "vaakapila@gmail.com"

        temp_pdf_path = f"/tmp/{project_id}_DailyLog.pdf"
        c = canvas.Canvas(temp_pdf_path)
        c.drawString(100, 750, f"Project ID: {project_id}")
        c.drawString(100, 730, f"Work Summary: {work_summary}")
        c.drawString(100, 710, f"Materials Used: {materials}")
        c.save()
        print("✅ [DEBUG] PDF created successfully.")

        # Email sending block
        msg = EmailMessage()
        msg['Subject'] = f'Daily Log Report - {project_id}'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg.set_content('Attached is your test Daily Log PDF.')

        with open(temp_pdf_path, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=f"{project_id}_DailyLog.pdf")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("📧 [DEBUG] Test Email sent successfully to:", recipient_email)

        return "✅ PDF test passed and email sent!"

    except Exception as e:
        print("❌ [DEBUG] Error during test PDF generation:", str(e))
        return "❌ Test Failed!"
