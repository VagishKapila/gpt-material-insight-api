import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log

app = Flask(__name__)

# Folder structure
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
    return render_template("form.html", current_date=datetime.utcnow().date())

@app.route("/generate_form", methods=["POST"])
def generate_form():
    session_id = str(uuid.uuid4())

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

    enable_ai = "enable_ai" in request.form
    image_paths = []
    ai_results = {}
    progress_report = {}

    # Save uploaded job site photos
    if "images" in request.files:
        for img in request.files.getlist("images"):
            if img and img.filename:
                filename = secure_filename(img.filename)
                path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
                img.save(path)
                image_paths.append(path)

    # Save logo
    logo_path = None
    if "logo" in request.files:
        logo = request.files["logo"]
        if logo and logo.filename:
            filename = secure_filename(logo.filename)
            logo_path = os.path.join(LOGO_FOLDER, f"{session_id}_{filename}")
            logo.save(logo_path)

    # Save safety sheet
    safety_sheet_path = None
    if "safety_sheet" in request.files:
        safety = request.files["safety_sheet"]
        if safety and safety.filename:
            filename = secure_filename(safety.filename)
            safety_sheet_path = os.path.join(SAFETY_FOLDER, f"{session_id}_{filename}")
            safety.save(safety_sheet_path)

    # Save scope file and run AI analysis
    scope_path = None
    if "scope_doc" in request.files:
        scope_doc = request.files["scope_doc"]
        if scope_doc and scope_doc.filename:
            filename = secure_filename(scope_doc.filename)
            scope_path = os.path.join(SCOPE_FOLDER, f"{session_id}_{filename}")
            scope_doc.save(scope_path)

            if enable_ai:
                ai_results = analyze_scope_vs_log(scope_path, form_data, image_paths)
                progress_report = ai_results.get("progress_report", {})

    # Save all session data to file
    session_data = {
        "form_data": form_data,
        "image_paths": image_paths,
        "logo_path": logo_path,
        "safety_sheet_path": safety_sheet_path,
        "ai_results": ai_results,
        "progress_report": progress_report,
        "weather_icon_path": None  # placeholder
    }

    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    with open(json_path, "w") as f:
        json.dump(session_data, f)

    return redirect(url_for("preview", session_id=session_id))

@app.route("/preview/<session_id>", methods=["GET"])
def preview(session_id):
    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if not os.path.exists(json_path):
        return "Session not found.", 404

    with open(json_path, "r") as f:
        data = json.load(f)

    return render_template("preview.html", **data, session_id=session_id)

@app.route("/submit_preview", methods=["POST"])
def submit_preview():
    session_id = request.form.get("session_id")
    if not session_id:
        return "Missing session ID", 400

    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if not os.path.exists(json_path):
        return "Session not found.", 404

    with open(json_path, "r") as f:
        data = json.load(f)

    try:
        total_items = int(request.form.get("total_items", 0))
        scored_items = []
        for i in range(total_items):
            scope = request.form.get(f"scope_{i}", "")
            confidence = int(request.form.get(f"confidence_{i}", 0))
            match = f"match_{i}" in request.form
            scored_items.append({"scope": scope, "confidence": confidence, "match": match})

        estimated_completion = sum(i["confidence"] for i in scored_items if i["match"]) / max(len(scored_items), 1)

        data["ai_results"] = {
            "completion": round(estimated_completion, 1),
            "scored_items": scored_items,
            "out_of_scope": data.get("ai_results", {}).get("out_of_scope", [])
        }
    except Exception as e:
        return f"Failed to process AI results: {str(e)}", 500

    # Generate final PDF
    pdf_name = f"{session_id}_daily_log.pdf"
    save_path = os.path.join(GENERATED_FOLDER, pdf_name)

    create_daily_log_pdf(
        data=data.get("form_data", {}),
        image_paths=data.get("image_paths", []),
        logo_path=data.get("logo_path"),
        ai_analysis=data.get("ai_results"),
        progress_report=data.get("progress_report"),
        save_path=save_path,
        weather_icon_path=data.get("weather_icon_path"),
        safety_sheet_path=data.get("safety_sheet_path")
    )

    return redirect(url_for("serve_pdf", filename=pdf_name))

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
