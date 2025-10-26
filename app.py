import os
import uuid
import json
from flask import Flask, request, send_from_directory, render_template, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import requests

from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import (
    analyze_scope_vs_log,
    load_scope_for_project,
    extract_scope_items,
    save_scope_for_project
)

# ---- CONFIG ----
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
AUTOFILL_FOLDER = "static/autofill"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
ALLOWED_SCOPE_EXTENSIONS = {"pdf", "docx", "doc", "xlsx"}

# ---- FLASK SETUP ----
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['SCOPE_FOLDER'] = SCOPE_FOLDER
app.config['AUTOFILL_FOLDER'] = AUTOFILL_FOLDER

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER, AUTOFILL_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

# ---- ROUTES ----
@app.route("/")
def health():
    return "✅ Daily Log AI is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    loc = request.args.get("location")
    if not loc:
        return jsonify({"weather": "No location"})
    try:
        r = requests.get(f"https://wttr.in/{loc}?format=3")
        return jsonify({"weather": r.text.strip()})
    except Exception:
        return jsonify({"weather": "Error fetching weather"})

@app.route("/generated/<filename>")
def serve_generated(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

@app.route("/generate_form", methods=["POST"])
def generate_form():
    form_data = request.form.to_dict()
    project_id = form_data.get("project_name", "project").replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_id = uuid.uuid4().hex[:8]
    pdf_filename = f"daily_log_{project_id}_{file_id}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, pdf_filename)

    # Upload logo
    logo_path = None
    logo_file = request.files.get("logo")
    if logo_file and allowed_file(logo_file.filename, ALLOWED_IMAGE_EXTENSIONS):
        logo_filename = f"logo_{file_id}.png"
        logo_path = os.path.join(UPLOAD_FOLDER, logo_filename)
        logo_file.save(logo_path)

    # Upload safety sheet
    safety_path = None
    safety_file = request.files.get("safety_sheet")
    if safety_file and allowed_file(safety_file.filename, ALLOWED_IMAGE_EXTENSIONS | {"pdf"}):
        ext = safety_file.filename.rsplit('.', 1)[1].lower()
        safety_filename = f"safety_{file_id}.{ext}"
        safety_path = os.path.join(UPLOAD_FOLDER, safety_filename)
        safety_file.save(safety_path)

    # Upload job images
    image_paths = []
    for img in request.files.getlist("images"):
        if img and allowed_file(img.filename, ALLOWED_IMAGE_EXTENSIONS):
            img_filename = f"img_{uuid.uuid4().hex[:6]}.jpg"
            img_path = os.path.join(UPLOAD_FOLDER, img_filename)
            img.save(img_path)
            image_paths.append(img_path)

    # Upload scope document (only used for initial upload)
    scope_file = request.files.get("scope_doc")
    if scope_file and allowed_file(scope_file.filename, ALLOWED_SCOPE_EXTENSIONS):
        scope_text = request.form.get("scope_text", "")
        scope_items = extract_scope_items(scope_text)
        if scope_items:
            save_scope_for_project(project_id, scope_items)

    # Load saved scope
    scope_items = load_scope_for_project(project_id)

    # AI Scope Comparison
    enable_ai = form_data.get("enable_ai") == "on"
    if enable_ai:
        ai_analysis = analyze_scope_vs_log(
            scope_items=scope_items,
            work_done=form_data.get("work_done", ""),
            crew_notes=form_data.get("crew_notes", ""),
            safety_notes=form_data.get("safety_notes", "")
        )
    else:
        ai_analysis = {}

    # Save autofill data for pre-fill next time
    with open(os.path.join(AUTOFILL_FOLDER, f"{project_id}.json"), "w") as f:
        json.dump(form_data, f)

    # Weather icon path (skip for now)
    weather_icon_path = None

    # Generate PDF
    create_daily_log_pdf(
        data=form_data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=ai_analysis,
        progress_report=None,
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_path
    )

    return {"pdf_url": f"/generated/{pdf_filename}"}

# ---- RUN ----
if __name__ == "__main__":
    app.run(debug=True)
