import os
from flask import Flask, request, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage
from io import BytesIO

app = Flask(__name__)

# ✅ ENV SETTINGS
SMTP_SERVER = "smtp.sendgrid.net"
SMTP_PORT = 587
SMTP_USERNAME = "apikey"
SMTP_PASSWORD = "your_sendgrid_api_key_here"  # ⛔ Replace with real API key securely or use os.environ["SENDGRID_API_KEY"]
FROM_EMAIL = "NNdailylogAI@gmail.com"
TO_EMAIL = "vaakapila@gmail.com"  # Change as needed

@app.route('/')
def home():
    return "Nails & Notes Daily Log API is live!"

@app.route('/send-test-email', methods=['GET'])
def send_test_email():
    try:
        # ✅ Generate test PDF in memory
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        c.drawString(100, 750, "Test PDF from Nails & Notes 🧠🛠️")
        c.save()
        pdf_buffer.seek(0)

        # ✅ Compose email with attachment
        msg = EmailMessage()
        msg["Subject"] = "🧾 Nails & Notes | Test PDF"
        msg["From"] = FROM_EMAIL
        msg["To"] = TO_EMAIL
        msg.set_content("Attached is a test PDF generated from the Nails & Notes Daily Log system.")

        # ✅ Attach PDF
        msg.add_attachment(
            pdf_buffer.read(),
            maintype="application",
            subtype="pdf",
            filename="NailsNotes_Test.pdf"
        )

        # ✅ Send via SendGrid SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return jsonify({"status": "✅ Email sent successfully!"})

    except Exception as e:
        print(f"❌ Email error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
