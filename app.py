from flask import Flask, request, send_file, render_template_string
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)

EMAIL_ADDRESS = "NNdailylogAI@gmail.com"
EMAIL_PASSWORD = "jvtemkdbvwbkijtz"  # App Password from Gmail

@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
        <h1>Nails & Notes - Daily Log Submission</h1>
        <form method=post enctype=multipart/form-data action="/generate-pdf">
          Project ID: <input type=text name=project_id value="proj-001"><br><br>
          Work Summary:<br><textarea name=work_summary rows=4 cols=50></textarea><br><br>
          Materials Used (comma separated): <input type=text name=materials><br><br>
          Your Email: <input type=text name=email><br><br>
          <input type=submit value="Generate & Email PDF">
        </form>
    """)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        print("✅ [DEBUG] Starting PDF generation...")

        # Collect form data
        form_data = request.form.to_dict()
        print("📥 [DEBUG] Form Data:", form_data)

        project_id = form_data.get("project_id", "Unknown Project")
        work_summary = form_data.get("work_summary", "No summary provided.")
        materials_used = form_data.get("materials_used", "None listed")
        recipient_email = form_data.get("email", "NNdailylogAI@gmail.com")

        # Create PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 750, f"Daily Log - Project: {project_id}")
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Work Summary: {work_summary}")
        c.drawString(50, 700, f"Materials Used: {materials_used}")
        c.save()
        pdf_buffer.seek(0)

        print("✅ [DEBUG] PDF created successfully.")

        # Save temp file for emailing
        temp_pdf_path = f"/tmp/{project_id.replace(' ', '_')}_DailyLog.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_buffer.read())
        print(f"💾 [DEBUG] PDF written to {temp_pdf_path}")

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
        print("❌ [ERROR] Failed during PDF/email flow:", str(e))
        return f"❌ Internal Server Error: {str(e)}", 500
    project_id = request.form.get("project_id")
    work_summary = request.form.get("work_summary")
    materials = request.form.get("materials")
    user_email = request.form.get("email")

    filename = f"{project_id}_daily_log.pdf"
    filepath = os.path.join("/tmp", filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, f"Project Daily Log - {project_id}")

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.5 * inch, "Work Summary:")
    text = c.beginText(1 * inch, height - 1.8 * inch)
    for line in work_summary.split("\n"):
        text.textLine(line)
    c.drawText(text)

    c.drawString(1 * inch, height - 3.2 * inch, f"Materials Used: {materials}")
    c.save()

    # Send the PDF to email
    if user_email:
        send_email_with_attachment(user_email, filepath, filename)

    return send_file(filepath, as_attachment=True)

def send_email_with_attachment(recipient, filepath, filename):
    msg = EmailMessage()
    msg["Subject"] = "Your Daily Construction Log PDF"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg.set_content("Attached is your Daily Log PDF from Nails & Notes.")

    with open(filepath, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
