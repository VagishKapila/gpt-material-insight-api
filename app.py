import os
import json
import uuid
import traceback
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

# --- Stable Import of AI only (no parse_scope_file) ---
from utils.compare_scope_vs_log import analyze_scope_vs_log

from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)

# --- Folders ---
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
SAFETY_FOLDER = "static/safety"
LOGO_FOLDER = "static/logo"
SESSION_FOLDER = "session_data"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER, SAFETY_FOLDER, LOGO_FOLDER, SESSION_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def health():
    return "✅ Nails & Notes AI Log is running!"

@app.route("/form")
def form():
    return render_template("form.html", datetime=datetime)

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = {
            "project_name": request.form.get("project_name"),
            "client_name": request.form.get("client_name"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "weather": request.form.get("weather"),
            "work_done": request.form.get("work_done"),
            "crew_notes": request.form.get("crew_notes"),
            "safety_notes": request.form.get("safety_notes")
        }

        session_id = str(uuid.uuid4())
        image_paths = []
        scope_path = None
        safety_path = None
        logo_path = None

        def save_file(field, folder):
            if field in request.files and request.files[field].filename:
                file = request.files[field]
                filename = secure_filename(file.filename)
                path = os.path.join(folder, f"{session_id}_{filename}")
                file.save(path)
                return path
            return None

        logo_path = save_file("logo", LOGO_FOLDER)
        safety_path = save_file("safety_sheet", SAFETY_FOLDER)
        scope_path = save_file("scope_doc", SCOPE_FOLDER)

        if "images" in request.files:
            for img in request.files.getlist("images"):
                if img.filename:
                    filename = secure_filename(img.filename)
                    path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
                    img.save(path)
                    image_paths.append(path)

        ai_results = {}
        progress_report = {}
        if request.form.get("enable_ai") and scope_path:
            try:
                ai_results = analyze_scope_vs_log(scope_path, form_data, image_paths)
            except Exception as e:
                traceback.print_exc()
                ai_results = {"error": f"AI analysis failed: {str(e)}"}

        session_data = {
            "form_data": form_data,
            "image_paths": image_paths,
            "logo_path": logo_path,
            "ai_results": ai_results,
            "progress_report": progress_report,
            "weather_icon_path": None,
            "safety_sheet_path": safety_path
        }

        session_file = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        print(f"
