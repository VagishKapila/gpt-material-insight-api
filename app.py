import os
import uuid
import json
import tempfile
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
from utils.pdf_generator import create_daily_log_pdf
from compare_scope_vs_log import analyze_scope_vs_log, parse_scope_file, load_scope_for_project

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
SCOPE_FOLDER = "scope"
GENERATED_FOLDER = "static/generated"
PREVIEW_FOLDER = "static/previews"
AUTOFILL_FOLDER = "static/autofill"

for folder in [UPLOAD_FOLDER, SCOPE_FOLDER, GENERATED_FOLDER, PREVIEW_FOLDER, AUTOFILL_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "pdf", "docx", "xlsx", "xls", "txt"}

@app.route("/")
def home():
    return "🛠️ Daily Log AI is Running"

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    import requests
    location = request.args.get("location", "")
    try:
        resp = requests.get(f"https://wttr.in/{location}?format=1", timeout=2)
        return resp.text.strip()
    except:
        return "Could not fetch"

@app.route("/generate_form", methods=["POST"])
def generate_form():
    data = request.form.to_dict()
    images = request.files.getlist("images")
    logo = request.files.get("logo")
    safety_sheet = request.files.get("safety_sheet")
    scope_file = request.files.get("scope_file")
    enable_ai = True if request.form.get("enable_ai") == "on" else False

    session_id = str(uuid.uuid4())
    project_id = data.get("Project", "default").strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    image_paths = []
    for file in images:
        if file and allowed_file(file.filename):
            path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{file.filename}")
            file.save(path)
            image_paths.append(path)

    logo_path = None
    if logo and allowed_file(logo.filename):
        logo_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_logo_{logo.filename}")
        logo.save(logo_path)

    safety_path = None
    if safety_sheet and allowed_file(safety_sheet.filename):
        safety_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_safety_{safety_sheet.filename}")
        safety_sheet.save(safety_path)

    if scope_file and allowed_file(scope_file.filename):
        scope_path = os.path.join(SCOPE_FOLDER, f"scope_{project_id}.txt")
        parsed_scope = parse_scope_file(scope_file)
        with open(scope_path, "w", encoding="utf-8") as f:
            f.write(parsed_scope)

    with open(os.path.join(AUTOFILL_FOLDER, f"{project_id}.json"), "w") as f:
        json.dump(data, f)

    scope_items = load_scope_for_project(project_id)
    ai_result = analyze_scope_vs_log(scope_items, data) if enable_ai else {}

    preview_data = {
        "session_id": session_id,
        "data": data,
        "image_paths": image_paths,
        "logo_path": logo_path,
        "safety_sheet_path": safety_path,
        "ai_result": ai_result,
        "project_id": project_id
    }

    # Safely convert non-serializable types
    def safe_json(obj):
        if isinstance(obj, (bool, int, float, str, type(None))):
            return obj
        if isinstance(obj, dict):
            return {k: safe_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [safe_json(x) for x in obj]
        return str(obj)

    preview_path = os.path.join(PREVIEW_FOLDER, f"{session_id}.json")
    with open(preview_path, "w") as f:
        json.dump(safe_json(preview_data), f)

    return redirect(url_for("preview", session_id=session_id))

@app.route("/preview/<session_id>")
def preview(session_id):
    try:
        preview_path = os.path.join(PREVIEW_FOLDER, f"{session_id}.json")
        with open(preview_path, "r") as f:
            context = json.load(f)

        return render_template("preview.html", **context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

@app.route("/generate_pdf/<session_id>")
def generate_pdf(session_id):
    try:
        with open(os.path.join(PREVIEW_FOLDER, f"{session_id}.json"), "r") as f:
            context = json.load(f)

        filename = f"daily_log_{session_id}.pdf"
        save_path = os.path.join(GENERATED_FOLDER, filename)

        create_daily_log_pdf(
            data=context.get("data"),
            image_paths=context.get("image_paths"),
            logo_path=context.get("logo_path"),
            ai_analysis=context.get("ai_result"),
            progress_report=context.get("ai_result"),
            save_path=save_path,
            safety_sheet_path=context.get("safety_sheet_path")
        )

        return redirect(f"/{save_path}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"PDF Generation Error: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
