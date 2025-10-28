# app.py

import os
import uuid
import json
import traceback
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

# ✅ Corrected imports from utils
from utils.compare_scope_vs_log import analyze_scope_vs_log, parse_scope_file, load_scope_for_project
from utils.pdf_generator import create_daily_log_pdf
from utils.weather_icon import get_weather_icon
from PIL import Image

app = Flask(__name__)

# ✅ Folder paths
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
AUTOFILL_FOLDER = "static/autofill"
SCOPE_FOLDER = "static/scope"
PREVIEW_FOLDER = "static/preview"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, AUTOFILL_FOLDER, SCOPE_FOLDER, PREVIEW_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def index():
    return "✅ Daily Log AI is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    icon_path = get_weather_icon(location)
    if icon_path:
        return icon_path
    return "", 404

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = request.form.to_dict()
        session_id = uuid.uuid4().hex

        # ✅ File uploads
        logo = request.files.get("logo")
        scope_file = request.files.get("scope_file")
        safety_sheet = request.files.get("safety_sheet")
        photos = request.files.getlist("images")

        def save_file(file_obj, folder):
            if not file_obj:
                return None
            filename = secure_filename(file_obj.filename)
            path = os.path.join(folder, f"{session_id}_{filename}")
            file_obj.save(path)
            return path

        logo_path = save_file(logo, UPLOAD_FOLDER)
        safety_sheet_path = save_file(safety_sheet, UPLOAD_FOLDER)

        image_paths = [save_file(photo, UPLOAD_FOLDER) for photo in photos if photo]

        # ✅ Handle scope
        project_id = form_data.get("Project", "default_project").strip().replace(" ", "_")
        scope_path = os.path.join(SCOPE_FOLDER, f"{project_id}.txt")

        if scope_file:
            uploaded_path = save_file(scope_file, SCOPE_FOLDER)
            parsed_scope = parse_scope_file(uploaded_path)
            with open(scope_path, "w", encoding="utf-8") as f:
                f.write("\n".join(parsed_scope))

        scope_text = load_scope_for_project(project_id)

        combined_text = "\n".join([
            form_data.get("Work Done", ""),
            form_data.get("Crew Notes", ""),
            form_data.get("Safety Notes", ""),
        ])

        ai_results = analyze_scope_vs_log(scope_text, combined_text)

        # ✅ Save preview data
        preview_data = {
            "session_id": session_id,
            "form_data": form_data,
            "logo_path": logo_path,
            "safety_sheet_path": safety_sheet_path,
            "image_paths": image_paths,
            "ai_results": ai_results,
            "project_id": project_id,
        }

        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "w") as f:
            json.dump(preview_data, f, indent=2, default=str)

        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Internal Server Error: {e}", 500

@app.route("/preview/<session_id>")
def preview(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            data = json.load(f)
        return render_template("preview.html", **data)
    except Exception as e:
        traceback.print_exc()
        return f"❌ Internal Server Error: {e}", 500

@app.route("/generate_pdf/<session_id>")
def generate_pdf(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            data = json.load(f)

        save_path = os.path.join(GENERATED_FOLDER, f"daily_log_{session_id}.pdf")

        create_daily_log_pdf(
            data=data["form_data"],
            image_paths=data["image_paths"],
            logo_path=data.get("logo_path"),
            ai_analysis=data.get("ai_results"),
            progress_report=data.get("ai_results"),
            save_path=save_path,
            weather_icon_path=None,
            safety_sheet_path=data.get("safety_sheet_path"),
        )

        return send_file(save_path, as_attachment=True)

    except Exception as e:
        traceback.print_exc()
        return f"❌ Internal Server Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
