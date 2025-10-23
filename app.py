from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
import os
import datetime
import uuid
import requests

app = Flask(__name__)

# ---- Folders ----
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(SCOPE_FOLDER, exist_ok=True)

# ---- In-memory project cache ----
PROJECT_CACHE = {}
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm", "csv", "txt", "jpg", "jpeg", "png", "gif"}

# ---- Utility ----
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def health_check():
    return "✅ Nails & Notes: Daily Log AI is running!"


@app.route("/form")
def form():
    project_id = request.args.get("project", "").strip().lower().replace(" ", "_")
    last_data = PROJECT_CACHE.get(project_id, {}) if project_id else {}
    return render_template("form.html", last_data=last_data)


@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    try:
        res = requests.get(f"https://wttr.in/{location}?format=3", timeout=5)
        return res.text.strip()
    except Exception:
        return "Could not fetch weather"


@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form = request.form.to_dict()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        project_id = form.get("project_name", "").strip().lower().replace(" ", "_") or str(uuid.uuid4())

        # ---- Restore saved fields ----
        if project_id in PROJECT_CACHE:
            for k, v in PROJECT_CACHE[project_id].items():
                if not form.get(k):
                    form[k] = v

        reusable_fields = [
            "project_name", "client_name", "location", "job_number",
            "crew_notes", "work_done", "safety_notes", "weather"
        ]
        PROJECT_CACHE[project_id] = {k: form.get(k, "") for k in reusable_fields}

        # ---- Save photos ----
        saved_photo_paths = []
        for file in request.files.getlist("images"):
            if file and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{fname}")
                file.save(path)
                saved_photo_paths.append(path)

        # ---- Save logo ----
        logo_path = None
        logo = request.files.get("logo")
        if logo and allowed_file(logo.filename):
            fname = secure_filename(logo.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, f"logo_{timestamp}_{fname}")
            logo.save(logo_path)

        # ---- Scope of Work (one-time) ----
        scope_path = None
        scope_file = request.files.get("scope_doc")
        scope_filename = f"{project_id}_scope"
        if scope_file and allowed_file(scope_file.filename):
            # Save only if not already stored
            for ext in ALLOWED_EXTENSIONS:
                candidate = os.path.join(SCOPE_FOLDER, f"{scope_filename}.{ext}")
                if os.path.exists(candidate):
                    scope_path = candidate
                    break
            if not scope_path:
                ext = os.path.splitext(scope_file.filename)[1]
                scope_path = os.path.join(SCOPE_FOLDER, f"{scope_filename}{ext}")
                scope_file.save(scope_path)

        # ---- Weather ----
        weather = form.get("weather", "")

        # ---- Enable AI/AR ----
        enable_ai_analysis = form.get("enable_ai", "on").lower() in ["on", "true", "yes", "1"]

        # ---- Output path ----
        output_pdf_path = os.path.join(GENERATED_FOLDER, f"DailyLog_{timestamp}.pdf")

        # ---- Generate PDF ----
        create_daily_log_pdf(
            form_data=form,
            photo_paths=saved_photo_paths,
            output_path=output_pdf_path,
            logo_path=logo_path,
            scope_path=scope_path,
            weather=weather,
            enable_ai_analysis=enable_ai_analysis
        )

        print(f"✅ PDF generated successfully: {output_pdf_path}")
        return jsonify({"pdf_url": f"/generated/{os.path.basename(output_pdf_path)}"})

    except Exception as e:
        print("🔥 ERROR generating log:", e)
        return "Internal Server Error", 500


@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)
