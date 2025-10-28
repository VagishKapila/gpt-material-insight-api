import os
import uuid
import json
import traceback
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
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


@app.route("/")
def index():
    return "✅ Daily Log AI is running."


@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    try:
        icon_path = get_weather_icon(location)
        return icon_path if icon_path else ("", 404)
    except Exception as e:
        print(f"[Weather] ⚠️ Error fetching icon: {e}")
        return "", 500


@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = request.form.to_dict()
        session_id = uuid.uuid4().hex

        def save_file(file_obj, folder):
            if file_obj and file_obj.filename:
                filename = secure_filename(file_obj.filename)
                path = os.path.join(folder, f"{session_id}_{filename}")
                file_obj.save(path)
                return path
            return None

        logo_path = save_file(request.files.get("logo"), UPLOAD_FOLDER)
        safety_path = save_file(request.files.get("safety_sheet"), UPLOAD_FOLDER)
        scope_file = request.files.get("scope_doc")

        image_paths = []
        for photo in request.files.getlist("images"):
            img_path = save_file(photo, UPLOAD_FOLDER)
            if img_path:
                image_paths.append(img_path)

        project_id = form_data.get("project_name", "default").replace(" ", "_").lower()
        scope_path = os.path.join(SCOPE_FOLDER, f"scope_{project_id}.txt")

        # Parse uploaded scope
        if scope_file:
            parsed = parse_scope_file(save_file(scope_file, SCOPE_FOLDER))
            lines = parsed.splitlines() if isinstance(parsed, str) else []
            with open(scope_path, "w", encoding="utf-8") as f:
                f.write("\n".join([line.strip() for line in lines if line.strip()]))

        enable_ai = form_data.get("enable_ai", "off") == "on"
        ai_results = None

        if enable_ai:
            scope_items = load_scope_for_project(project_id)
            combined_text = "\n".join([
                form_data.get("work_done", ""),
                form_data.get("crew_notes", ""),
                form_data.get("safety_notes", "")
            ])
            ai_results = analyze_scope_vs_log(scope_items, combined_text)

        preview_data = {
            "session_id": session_id,
            "form_data": form_data,
            "image_paths": image_paths,
            "logo_path": logo_path,
            "safety_sheet_path": safety_path,
            "ai_results": ai_results,
            "project_id": project_id
        }

        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "w") as f:
            json.dump(preview_data, f, indent=2)

        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error generating form: {e}", 500


@app.route("/preview/<session_id>")
def preview(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            data = json.load(f)
        return render_template("preview.html", **data)
    except Exception as e:
        traceback.print_exc()
        return f"❌ Error loading preview: {e}", 500


@app.route("/generate_pdf/<session_id>", methods=["POST"])
def generate_pdf(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            data = json.load(f)

        override = request.form.get("override_completion")
        progress = data.get("ai_results", {}) or {}
        if override:
            try:
                progress["completion"] = int(override)
                progress["user_override"] = True
                print(f"🧭 Override completion: {override}%")
            except Exception as e:
                print(f"⚠️ Invalid override value: {override} ({e})")

        save_path = os.path.join(GENERATED_FOLDER, f"{session_id}_daily_log.pdf")

        create_daily_log_pdf(
            data=data["form_data"],
            image_paths=data["image_paths"],
            logo_path=data.get("logo_path"),
            ai_analysis=data.get("ai_results"),
            progress_report=progress,
            save_path=save_path,
            weather_icon_path=None,
            safety_sheet_path=data.get("safety_sheet_path")
        )

        return send_file(save_path, as_attachment=True)

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error generating PDF: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
