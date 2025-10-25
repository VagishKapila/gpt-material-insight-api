import os
import json
from flask import Flask, request, send_from_directory, render_template
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import compare_scope_with_log
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
SCOPE_FOLDER = "static/scope"
GENERATED_FOLDER = "static/generated"
DEBUG_FOLDER = "debug_output"

# Ensure all folders exist
for folder in [UPLOAD_FOLDER, SCOPE_FOLDER, GENERATED_FOLDER, DEBUG_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def index():
    return "✅ Nails & Notes Daily Log AI is up and running!"

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    data = {
        key: request.form.get(key, "") for key in [
            "project_name", "client_name", "location", "date", "weather",
            "crew_notes", "work_done", "safety_notes"
        ]
    }

    enable_ai = "enable_ai" in request.form
    print(f"🔍 AI Scope Analysis Enabled: {enable_ai}")

    # Handle file uploads
    uploaded_images = request.files.getlist("images")
    image_paths = []
    for file in uploaded_images:
        if file:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            image_paths.append(path)

    logo_path = None
    logo_file = request.files.get("logo")
    if logo_file and logo_file.filename:
        logo_path = os.path.join(UPLOAD_FOLDER, secure_filename(logo_file.filename))
        logo_file.save(logo_path)

    safety_sheet_path = None
    safety_file = request.files.get("safety_sheet")
    if safety_file and safety_file.filename:
        safety_sheet_path = os.path.join(UPLOAD_FOLDER, secure_filename(safety_file.filename))
        safety_file.save(safety_sheet_path)

    scope_path = None
    scope_file = request.files.get("scope_doc")
    if scope_file and scope_file.filename:
        scope_path = os.path.join(SCOPE_FOLDER, secure_filename(scope_file.filename))
        scope_file.save(scope_path)

    # Run AI logic if enabled and scope exists
    progress_report = {}
    if enable_ai and scope_path and data.get("work_done"):
        # Convert scope to JSON if needed
        from utils.convert_scope_to_json import convert_scope_to_json
        scope_json_path = convert_scope_to_json(scope_path)
        log_text = data.get("work_done", "") + "\n" + data.get("crew_notes", "")
        progress_report = compare_scope_with_log(scope_json_path, log_text, debug_save=True)

    # Final save path
    filename = f"DailyLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, filename)

    create_daily_log_pdf(
        data=data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=enable_ai,
        progress_report=progress_report,
        save_path=save_path,
        weather_icon_path=None,
        safety_sheet_path=safety_sheet_path
    )

    return f"<p>✅ PDF generated: <a href='/static/generated/{filename}' target='_blank'>{filename}</a></p>"

if __name__ == "__main__":
    app.run(debug=True)
