# FULL app.py integrated with updated PDF generator

import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import compare_scope_with_log
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import docx
import requests

app = Flask(__name__)

# === Folders ===
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
AUTOFILL_FOLDER = "static/autofill"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(SCOPE_FOLDER, exist_ok=True)
os.makedirs(AUTOFILL_FOLDER, exist_ok=True)

# === ROUTES ===
@app.route("/")
def index():
    return "Nails & Notes App is running."

@app.route("/form")
def form():
    return render_template("form.html")

# === WEATHER ===
@app.route("/get_weather", methods=["POST"])
def get_weather():
    location = request.form.get("location")
    try:
        res = requests.get(f"https://wttr.in/{location}?format=%C+%t", timeout=5)
        weather = res.text.strip()
        return jsonify({"weather": weather})
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return jsonify({"weather": "Unavailable"})

# === FORM SUBMISSION ===
@app.route("/generate_form", methods=["POST"])
def generate_form():
    form_data = request.form.to_dict()
    files = request.files

    image_paths = []
    if "images" in files:
        for f in request.files.getlist("images"):
            filename = secure_filename(f.filename)
            if not filename:
                continue
            path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
            f.save(path)
            image_paths.append(path)

    logo_path = None
    if "logo" in files:
        f = files["logo"]
        if f.filename:
            logo_path = os.path.join(UPLOAD_FOLDER, f"logo_{uuid.uuid4().hex}_{secure_filename(f.filename)}")
            f.save(logo_path)

    safety_sheet_path = None
    if "safety_sheet" in files:
        f = files["safety_sheet"]
        if f.filename:
            safety_sheet_path = os.path.join(UPLOAD_FOLDER, f"safety_{uuid.uuid4().hex}_{secure_filename(f.filename)}")
            f.save(safety_sheet_path)

    weather_icon_path = None

    scope_result = None
    project_name = form_data.get("project_name", "default_project").replace(" ", "_")
    scope_path = os.path.join(SCOPE_FOLDER, f"{project_name}_scope.txt")
    scope_text = None

    if os.path.exists(scope_path):
        with open(scope_path, "r") as f:
            scope_text = f.read()
    elif "scope_doc" in files:
        f = files["scope_doc"]
        if f.filename:
            ext = os.path.splitext(f.filename)[1].lower()
            new_path = os.path.join(SCOPE_FOLDER, secure_filename(f.filename))
            f.save(new_path)
            scope_text = extract_text_from_file(new_path)
            with open(scope_path, "w") as f:
                f.write(scope_text)

    if form_data.get("enable_ai") == "on" and scope_text:
        scope_result = compare_scope_with_log(scope_path, form_data.get("work_done", ""))

    filename = f"DailyLog_{uuid.uuid4().hex[:6]}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, filename)
    create_daily_log_pdf(
        form_data,
        image_paths,
        logo_path,
        ai_analysis=True,
        progress_report=scope_result,
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_sheet_path
    )

    return jsonify({"pdf_url": f"/generated/{filename}"})

@app.route("/generated/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".pdf":
            text = ""
            with open(filepath, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        elif ext in [".doc", ".docx"]:
            doc = docx.Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext == ".txt":
            with open(filepath, "r") as f:
                return f.read()
    except Exception as e:
        print(f"File extraction failed: {e}")
    return ""

if __name__ == "__main__":
    app.run(debug=True)
