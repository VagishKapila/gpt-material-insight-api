import os
import json
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime

from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log

app = Flask(__name__)

# Folder paths
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
SAFETY_FOLDER = "static/safety"
LOGO_FOLDER = "static/logo"
SESSION_FOLDER = "session_data"

# Create folders if not exist
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
    # Parse form fields
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

    # Handle image uploads
    image_paths = []
    for img_file in request.files.getlist("images"):
        if img_file and img_file.filename:
            filename = secure_filename(img_file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            img_file.save(save_path)
            image_paths.append(save_path)

    # Handle scope file
    scope_path = None
    scope_file = request.files.get("scope_doc")
    if scope_file and scope_file.filename:
        filename = secure_filename(scope_file.filename)
        scope_path = os.path.join(SCOPE_FOLDER, filename)
        scope_file.save(scope_path)

    # Handle safety sheet
    safety_path = None
    safety_file = request.files.get("safety_sheet")
    if safety_file and safety_file.filename:
        filename = secure_filename(safety_file.filename)
        safety_path = os.path.join(SAFETY_FOLDER, filename)
        safety_file.save(safety_path)

    # Handle logo
    logo_path = None
    logo_file = request.files.get("logo")
    if logo_file and logo_file.filename:
        filename = secure_filename(logo_file.filename)
        logo_path = os.path.join(LOGO_FOLDER, filename)
        logo_file.save(logo_path)

    # Run AI analysis (optional)
    ai_enabled = "enable_ai" in request.form
    ai_results = {}
    if ai_enabled and scope_path:
        ai_results = analyze_scope_vs_log(scope_path, form_data, image_paths)

    # Save session data for preview
    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "form_data": form_data,
        "image_paths": image_paths,
        "logo_path": logo_path,
        "safety_sheet_path": safety_path,
        "weather_icon_path": None,
        "ai_results": ai_results,
        "progress_report": None
    }

    with open(os.path.join(SESSION_FOLDER, f"{session_id}.json"), "w") as f:
        json.dump(session_data, f)

    return redirect(url_for("preview", session_id=session_id))

@app.route("/preview/<session_id>")
def preview(session_id):
    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if not os.path.exists(json_path):
        return "Session not found.", 404

    with open(json_path, "r") as f:
        data = json.load(f)

    return render_template("preview.html", **data)

@app.route("/submit_preview", methods=["POST"])
def submit_preview():
    session_id = request.form.get("session_id")
    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if not os.path.exists(json_path):
        return "Session not found.", 404

    with open(json_path, "r") as f:
        data = json.load(f)

    # Update AI results from form
    try:
        total_items = int(request.form.get("total_items", 0))
        scored_items = []
        for i in range(total_items):
            scope = request.form.get(f"scope_{i}", "")
            confidence = int(request.form.get(f"confidence_{i}", 0))
            match = f"match_{i}" in request.form
            scored_items.append({"scope": scope, "confidence": confidence, "match": match})

        # Calculate updated completion %
        matched = [item["confidence"] for item in scored_items if item["match"]]
        completion = round(sum(matched) / len(scored_items), 1) if scored_items else 0

        data["ai_results"] = {
            "completion": completion,
            "scored_items": scored_items,
            "out_of_scope": data.get("ai_results", {}).get("out_of_scope", [])
        }
    except Exception as e:
        return f"Error processing AI updates: {str(e)}", 500

    # Generate PDF
    pdf_filename = f"{session_id}_daily_log.pdf"
    save_path = os.path.join(GENERATED_FOLDER, pdf_filename)

    create_daily_log_pdf(
        data=data["form_data"],
        image_paths=data["image_paths"],
        logo_path=data["logo_path"],
        ai_analysis=data["ai_results"],
        progress_report=data.get("progress_report"),
        save_path=save_path,
        weather_icon_path=data.get("weather_icon_path"),
        safety_sheet_path=data.get("safety_sheet_path")
    )

    return redirect(url_for("serve_pdf", filename=pdf_filename))

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
