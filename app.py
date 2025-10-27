from flask import Flask, request, jsonify
from utils.pdf_generator import create_daily_log_pdf
from compare_scope_vs_log import analyze_scope_vs_log, load_scope_for_project
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "scope"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def index():
    return "✅ Daily Log AI is running."

@app.route("/generate", methods=["POST"])
def generate_log():
    try:
        data = request.json
        project_id = data.get("project_id", "default")
        scope_items = load_scope_for_project(project_id)

        ai_analysis = analyze_scope_vs_log(scope_items, data)

        filename = f"log_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(GENERATED_FOLDER, filename)

        create_daily_log_pdf(
            data=data,
            image_paths=[],  # Extend later if needed
            logo_path=None,
            ai_analysis=ai_analysis,
            progress_report=None,
            save_path=pdf_path,
            weather_icon_path=None,
            safety_sheet_path=None
        )

        return jsonify({"pdf_url": f"/generated/{filename}"}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/upload_scope_txt", methods=["POST"])
def upload_scope_txt():
    try:
        content = request.json
        project_id = content.get("project_id")
        scope_lines = content.get("scope_items", [])

        if not project_id or not scope_lines:
            return jsonify({"error": "Missing project_id or scope_items"}), 400

        path = os.path.join(SCOPE_FOLDER, f"scope_{project_id}.txt")
        with open(path, "w", encoding="utf-8") as f:
            for line in scope_lines:
                f.write(line.strip() + "\n")

        return jsonify({"message": f"Scope saved for project {project_id}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return app.send_static_file(f"generated/{filename}")
