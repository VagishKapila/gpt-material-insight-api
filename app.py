from flask import Flask, request
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage
import os
import io

app = Flask(__name__)

# Load environment variables (used for both real and dummy routes)
EMAIL_ADDRESS = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASS")

@app.route("/")
def index():
    return "<h1>Nails & Notes: Daily Log API is Running!</h1>"

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        print("✅ [DEBUG] Starting PDF generation...")

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

        # Save to file
        temp_pdf_path = f"/tmp/{project_id}_DailyLog.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(buffer.read())
        print("💾 [DEBUG] PDF written to", temp_pdf_path)

        # Send Email
        print(f"📤 [DEBUG] Sending email to: {recipient_email}")
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
    try:
        print("✅ [DEBUG] Starting test PDF generation...")

        # Create test PDF in memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "📄 This is a test PDF document.")
        c.save()
        buffer.seek(0)
        print("✅ [DEBUG] Test PDF created successfully.")

        # Get recipient from env or default
        recipient_email = os.getenv('TEST_EMAIL', 'vaakapila@gmail.com')
        print("📤 [DEBUG] Sending test email to:", recipient_email)

        # Use global email vars
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            raise ValueError("EMAIL credentials missing in environment!")

        msg = EmailMessage()
        msg['Subject'] = 'Test Daily Log PDF'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg.set_content('Attached is your test Daily Log PDF.')
        msg.add_attachment(buffer.read(), maintype='application', subtype='pdf', filename="Test_DailyLog.pdf")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        print("📧 [DEBUG] Test email sent successfully!")
        return "✅ PDF test passed and email sent!"

    except Exception as e:
        print("❌ [ERROR] Test route failed:", str(e))
        return f"❌ Internal error: {str(e)}", 500
