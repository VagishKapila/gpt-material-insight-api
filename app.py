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
