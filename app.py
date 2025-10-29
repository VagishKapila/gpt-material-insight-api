import os
import json
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from datetime import datetime
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 🔒 Bonus: Make datetime globally available in all Jinja templates
app.jinja_env.globals['datetime'] = datetime

# Folder setup
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
SAFETY_FOLDER = "static/safety"
LOGO_FOLDER = "static/logo"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER, SAFETY_FOLDER, LOGO_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def health():
    return "✅ Nails & Notes AI Log is running!"

@app.route("/form")
def form():
    return render_template("form.html")  # datetime now available via global

@app.route("/preview/<session_id>", methods=["GET"])
def preview(session_id):
    json_path = os.path.join("session_data", f"{session_id}.json")
    if not os.path.exists(json_path):
        return "Session not found.", 404

    with open(json_path, "r") as f:
        data = json.load(f)

    return render_template("preview.html", **data)

@app.route("/submit_preview", methods=["POST"])
def submit_preview():
    session_id = request.form.get("session_id")
    if not session_id:
        return "Missing session ID", 400

    json_path = os.path.join("session_data", f"{session_id}.json")
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
