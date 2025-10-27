from flask import Flask, request, jsonify
from utils.pdf_generator import create_daily_log_pdf
from compare_scope_vs_log import analyze_scope_vs_log
import os
import uuid
import json

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def index():
    return "Daily Log AI is running."

@app.route("/generate", methods=["POST"])
def generate_log():
    try:
        data = request.json

        # Input validation
        required_fields = ["project_name", "date", "location", "work_done", "crew_notes", "safety_notes"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        project_id = data.get("project_id", "default")
        scope_path = os.path.join(SCOPE_FOLDER, f"{project_id}.json")

        # AI Analysis
        ai_analysis = None
        if os.path.exists(scope_path):
            with open(scope_path, "r") as f:
                scope_data = json.load(f)
            ai_analysis = analyze_scope_vs_log(scope_data, data)

        # PDF Generation
        filename = f"log_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(GENERATED_FOLDER, filename)

        create_daily_log_pdf(
            data=data,
            image_paths=[],  # update to use if you send photo paths
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

@app.route("/upload_scope", methods=["POST"])
def upload_scope():
    try:
        content = request.json
        project_id = content.get("project_id")
        scope = content.get("scope_items", [])

        if not project_id or not scope:
            return jsonify({"error": "Missing project_id or scope_items"}), 400

        save_path = os.path.join(SCOPE_FOLDER, f"{project_id}.json")
        with open(save_path, "w") as f:
            json.dump(scope, f)

        return jsonify({"message": "Scope saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return app.send_static_file(f"generated/{filename}")
