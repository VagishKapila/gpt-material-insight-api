from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
import os
import datetime
import uuid
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret")

# --- Directories ---
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope_docs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(SCOPE_FOLDER, exist_ok=True)

# --- Allowed file extensions ---
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm", "csv", "txt", "png", "jpg", "jpeg"}

# --- In-memory cache for per-project data ---
PROJECT_CACHE = {}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_scope_path(project_id):
    """Return previously saved scope file if exists"""
    for ext in ALLOWED_EXTENSIONS:
        candidate = os.path.join(SCOPE_FOLDER, f"{project_id}_scope.{ext}")
        if os.path.exists(candidate):
            return candidate
    return None

@app.route("/")
def health():
    return "✅ Nails & Notes: Daily Log AI is live and running."

@app.route("/form")
def form():
    project_name = request.args.get("project_name", "").strip().lower().replace(" ", "_")
    last_data = PROJECT_CACHE.get(project_name, {})
    return render_template("form.html", last_data=last_data)

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return "N/A"
    try:
        response = requests.get(f"https://wttr.in/{location}?format=%l:+%t", timeout=4)
        return response.text.strip()
    except:
        return "N/A"

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = request.form.to_dict()
        project_id = form_data.get("project_name", "default_project").strip().lower().replace(" ", "_")

        # Restore cached fields
        if project_id in PROJECT_CACHE:
            cached = PROJECT_CACHE[project_id]
            for key, val in cached.items():
                if not form_data.get(key):
                    form_data[key] = val

        # Save current fields for next session autofill
        cache_fields = ["project_name", "location", "crew_notes", "work_done", "safety_notes", "weather"]
        PROJECT_CACHE[project_id] = {key: form_data.get(key, "") for key in cache_fields}

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # --- Save Photos ---
        photo_paths = []
        for file in request.files.getlist("images"):
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{timestamp}_{uuid.uuid4().hex}_{file.filename}")
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)
                photo_paths.append(path)

        # --- Save Logo (optional) ---
        logo_file = request.files.get("logo")
        logo_path = None
        if logo_file and allowed_file(logo_file.filename):
            logo_filename = secure_filename(f"logo_{timestamp}_{logo_file.filename}")
            logo_path = os.path.join(UPLOAD_FOLDER, logo_filename)
            logo_file.save(logo_path)

        # --- Scope of Work (one-time upload) ---
        scope_file = request.files.get("scope_doc")
        scope_path = get_scope_path(project_id)
        if scope_file and allowed_file(scope_file.filename) and not scope_path:
            ext = scope_file.filename.rsplit(".", 1)[1].lower()
            scope_filename = secure_filename(f"{project_id}_scope.{ext}")
            scope_path = os.path.join(SCOPE_FOLDER, scope_filename)
            scope_file.save(scope_path)

        # --- Generate PDF ---
        output_pdf_path = os.path.join(GENERATED_FOLDER, f"DailyLog_{timestamp}.pdf")

        create_daily_log_pdf(
            data=form_data,
            image_paths=photo_paths,
            pdf_path=output_pdf_path,
            logo_path=logo_path,
            scope_path=scope_path,
            enable_ai_analysis=form_data.get("enable_ai", "on").lower() in ["on", "true", "1"]
        )

        print(f"✅ PDF generated successfully: {output_pdf_path}")
        return jsonify({"pdf_url": f"/generated/{os.path.basename(output_pdf_path)}"})

    except Exception as e:
        print("🔥 ERROR generating log:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
