import os
import uuid
import json
import traceback
import numpy as np
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from utils.compare_scope_vs_log import analyze_scope_vs_log, parse_scope_file, load_scope_for_project
from utils.pdf_generator import create_daily_log_pdf
from utils.weather_icon import get_weather_icon

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
PREVIEW_FOLDER = "static/preview"
SCOPE_FOLDER = "static/scope"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, PREVIEW_FOLDER, SCOPE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# --- Handle NumPy bools for JSON ---
def convert_np_bools(obj):
    if isinstance(obj, dict):
        return {k: convert_np_bools(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_np_bools(i) for i in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

@app.route("/")
def index():
    return "✅ Daily Log AI is running"

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    icon_path = get_weather_icon(location)
    return icon_path if icon_path else ("", 404)

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = request.form.to_dict()
        session_id = uuid.uuid4().hex

        def save_file(file_obj, folder):
            if file_obj:
                filename = secure_filename(file_obj.filename)
                path = os.path.join(folder, f"{session_id}_{filename}")
                file_obj.save(path)
                return path
            return None

        logo_path = save_file(request.files.get("logo"), UPLOAD_FOLDER)
        safety_path = save_file(request.files.get("safety_sheet"), UPLOAD_FOLDER)

        scope_file = request.files.get("scope_doc")
        image_paths = [save_file(photo, UPLOAD_FOLDER) for photo in request.files.getlist("images") if photo]

        project_id = form_data.get("project_name", "default").replace(" ", "_").lower()
        scope_path = os.path.join(SCOPE_FOLDER, f"scope_{project_id}.txt")

        if scope_file:
            parsed = parse_scope_file(save_file(scope_file, SCOPE_FOLDER))
            parsed_lines = [line.strip() for line in parsed.splitlines() if line.strip()] if isinstance(parsed, str) else []
            with open(scope_path, "w", encoding="utf-8") as f:
                f.write("\n".join(parsed_lines))

        enable_ai = form_data.get("enable_ai", "off") == "on"
        ai_results = None

        if enable_ai:
            scope_items = load_scope_for_project(project_id)
            raw_results = analyze_scope_vs_log(scope_items, {
                "work_done": form_data.get("work_done", ""),
                "crew_notes": form_data.get("crew_notes", ""),
                "safety_notes": form_data.get("safety_notes", "")
            })
            ai_results = convert_np_bools(raw_results)

        preview_data = {
            "session_id": session_id,
            "form_data": form_data,
            "image_paths": image_paths,
            "logo_path": logo_path,
            "safety_sheet_path": safety_path,
            "ai_results": ai_results,
            "project_id": project_id
        }

        # Save to JSON
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "w") as f:
            json.dump(preview_data, f, indent=2)

        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error: {e}", 500

@app.route("/preview/<session_id>")
def preview(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            data = json.load(f)
        return render_template("preview.html", **data)
    except Exception as e:
        traceback.print_exc()
        return f"❌ Error: {e}", 500

@app.route("/generate_pdf/<session_id>", methods=["POST"])
def generate_pdf(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            data = json.load(f)

        # Check for user-edited confidence or match values
        edited_results = {
            "completion": float(request.form.get("completion", 0)),
            "scored_items": [],
            "out_of_scope": data["ai_results"].get("out_of_scope", [])
        }

        # Parse edited per-item AI results
        for i, item in enumerate(data["ai_results"].get("scored_items", [])):
            edited_conf = float(request.form.get(f"confidence_{i}", item["confidence"]))
            edited_match = request.form.get(f"match_{i}", "off") == "on"
            edited_results["scored_items"].append({
                "scope": item["scope"],
                "confidence": edited_conf,
                "match": edited_match
            })

        save_path = os.path.join(GENERATED_FOLDER, f"{session_id}_daily_log.pdf")

        create_daily_log_pdf(
            data=data["form_data"],
            image_paths=data["image_paths"],
            logo_path=data.get("logo_path"),
            ai_analysis=edited_results,
            progress_report=edited_results,
            save_path=save_path,
            weather_icon_path=None,
            safety_sheet_path=data.get("safety_sheet_path")
        )

        return send_file(save_path, as_attachment=True)

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
