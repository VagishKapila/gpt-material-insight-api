import os
from flask import Flask, request, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage
from io import BytesIO

app = Flask(__name__)

# ✅ HARD-CODED SETTINGS (For now — move to .env in production)
SMTP_SERVER = "smtp.sendgrid.net"
SMTP_PORT = 587
SMTP_USERNAME = "apikey"
SMTP_PASSWORD = "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"
FROM_EMAIL = "NNdailylogAI@gmail.com"
TO_EMAIL = "vaakapila@gmail.com"  # You can change this dynamically later

@app.route('/')
def home():
    return "🚀 Nails & Notes API is running!"

@app.route('/send-test-email', methods=['GET'])
def send_test_email():
    try:
        # ✅ Generate PDF in memory
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        c.drawString(100, 750, "🧠 Nails & Notes Test PDF")
        c.save()
        pdf_buffer.seek(0)

        # ✅ Compose email
        msg = EmailMessage()
        msg["Subject"] = "🧾 Nails & Notes | Test PDF"
        msg["From"] = FROM_EMAIL
        msg["To"] = TO_EMAIL
        msg.set_content("Hi there,\n\nAttached is a test PDF from the Nails & Notes Daily Log AI system.")

        # ✅ Attach the generated PDF
        msg.add_attachment(
            pdf_buffer.read(),
            maintype="application",
            subtype="pdf",
            filename="NailsNotes_Test.pdf"
        )

        # ✅ Send via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return jsonify({"status": "✅ Test email sent successfully!"})

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
