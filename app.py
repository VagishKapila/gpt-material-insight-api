
from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import json
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
SCOPE_FOLDER = 'static/scope'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(SCOPE_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "🛠️ Nails & Notes Daily Log AI is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/preview/<session_id>")
def preview(session_id):
    session_path = f"static/sessions/{session_id}.json"
    if not os.path.exists(session_path):
        return "Session not found.", 404

    with open(session_path) as f:
        session_data = json.load(f)

    return render_template(
        "preview.html",
        form_data=session_data.get("form_data", {}),
        image_paths=session_data.get("image_paths", []),
        ai_analysis=session_data.get("ai_analysis", {}),
        safety_sheet_path=session_data.get("safety_sheet_path", "")
    )

@app.route("/generate_form", methods=["POST"])
def generate_form():
    # Load session_id from cookie or previous session
    session_id = request.args.get("session_id")
    if not session_id:
        return "Missing session ID", 400

    session_path = f"static/sessions/{session_id}.json"
    if not os.path.exists(session_path):
        return "Session not found", 404

    with open(session_path) as f:
        session_data = json.load(f)

    form_data = session_data.get("form_data", {})
    image_paths = session_data.get("image_paths", [])
    logo_path = session_data.get("logo_path", "")
    safety_sheet_path = session_data.get("safety_sheet_path", "")
    ai_analysis = session_data.get("ai_analysis", {})
    save_path = os.path.join(GENERATED_FOLDER, f"{session_id}_final_log.pdf")

    create_daily_log_pdf(
        form_data,
        image_paths,
        logo_path,
        ai_analysis,
        progress_report=None,
        save_path=save_path,
        safety_sheet_path=safety_sheet_path
    )

    return redirect(url_for("serve_pdf", filename=f"{session_id}_final_log.pdf"))

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_file(os.path.join(GENERATED_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
