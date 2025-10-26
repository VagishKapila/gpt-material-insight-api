from flask import Flask, render_template, request, send_file, jsonify
from utils.pdf_generator import create_daily_log_pdf
from werkzeug.utils import secure_filename
import os
import datetime

app = Flask(__name__)

# Create necessary folders if they don't exist
os.makedirs("static/generated", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/scope", exist_ok=True)

@app.route("/")
def home():
    return "✅ Nails & Notes Daily Log API is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    data = request.form.to_dict()

    # File uploads
    images = request.files.getlist("images")
    logo = request.files.get("logo")
    safety_sheet = request.files.get("safety_sheet")
    scope_file = request.files.get("scope_doc")

    # Save images
    image_paths = []
    for image in images:
        if image:
            filename = secure_filename(image.filename)
            save_path = os.path.join("static/uploads", filename)
            image.save(save_path)
            image_paths.append(save_path)

    # Save logo
    logo_path = None
    if logo and logo.filename != "":
        logo_filename = secure_filename(logo.filename)
        logo_path = os.path.join("static/uploads", logo_filename)
        logo.save(logo_path)

    # Save safety sheet
    safety_sheet_path = None
    if safety_sheet and safety_sheet.filename != "":
        sheet_filename = secure_filename(safety_sheet.filename)
        safety_sheet_path = os.path.join("static/uploads", sheet_filename)
        safety_sheet.save(safety_sheet_path)

    # Save scope file
    progress_report = None
    if scope_file and scope_file.filename != "":
        scope_filename = secure_filename(scope_file.filename)
        scope_path = os.path.join("static/scope", scope_filename)
        scope_file.save(scope_path)
        data["scope_file_path"] = scope_path
        data["project_id"] = data.get("project_name", "default").replace(" ", "_")
        progress_report = scope_path  # passed to PDF gen later

    # AI checkbox
    ai_analysis = request.form.get("enable_ai", "on") == "on"

    # Final file path
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"log_{timestamp}.pdf"
    save_path = os.path.join("static/generated", pdf_filename)

    # Call PDF generator
    create_daily_log_pdf(
        data=data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=ai_analysis,
        progress_report=progress_report,
        save_path=save_path,
        safety_sheet_path=safety_sheet_path
    )

    return jsonify({"pdf_url": f"/generated/{pdf_filename}"})

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_file(os.path.join("static/generated", filename), as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
