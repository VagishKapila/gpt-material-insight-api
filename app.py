from flask import Flask, request, jsonify, render_template
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log, load_scope_for_project

import os
import uuid
import fitz  # PyMuPDF
import docx  # python-docx

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "scope"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ✅ Optional Debug Print to Confirm Folder Structure on Deploy
print("🛠️ [Startup Debug] Current Working Directory:", os.getcwd())
print("🛠️ [Startup Debug] Files in root:", os.listdir("."))
print("🛠️ [Startup Debug] Files in utils/:", os.listdir("utils"))
print("🛠️ [Startup Debug] Files in static/:", os.listdir("static") if os.path.exists("static") else "Missing 'static/' folder")
print("🛠️ [Startup Debug] Python Path:", os.sys.path)

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

@app.route("/generate_form", methods=["POST"])
def generate_from_form():
    try:
        form = request.form
        files = request.files

        project_name = form.get("project_name", "")
        client_name = form.get("client_name", "")
        location = form.get("location", "")
        date = form.get("date", "")
        weather = form.get("weather", "")
        work_done = form.get("work_done", "")
        safety_notes = form.get("safety_notes", "")
        enable_ai = form.get("enable_ai") == "on"

        project_id = project_name.replace(" ", "_").lower()

        # Save and parse scope file
        scope_file = files.get("scope_doc")
        if scope_file and scope_file.filename:
            ext = os.path.splitext(scope_file.filename)[1].lower()
            extracted_text = ""

            if ext == ".pdf":
                with fitz.open(stream=scope_file.stream.read(), filetype="pdf") as doc:
                    extracted_text = "\n".join(page.get_text() for page in doc)

            elif ext in [".docx"]:
                doc = docx.Document(scope_file)
                extracted_text = "\n".join(p.text for p in doc.paragraphs)

            elif ext == ".txt":
                extracted_text = scope_file.read().decode("utf-8")

            if extracted_text:
                txt_path = os.path.join("scope", f"scope_{project_id}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)

        # Save logo
        logo_file = files.get("logo")
        logo_path = None
        if logo_file and logo_file.filename:
            logo_path = os.path.join("static/uploads", f"logo_{uuid.uuid4().hex}.png")
            logo_file.save(logo_path)

        # Save safety sheet
        safety_file = files.get("safety_sheet")
        safety_path = None
        if safety_file and safety_file.filename:
            safety_path = os.path.join("static/uploads", f"safety_{uuid.uuid4().hex}.pdf")
            safety_file.save(safety_path)

        # Save jobsite images
        image_paths = []
        images = request.files.getlist("images")
        for img in images:
            if img.filename:
                img_path = os.path.join("static/uploads", f"img_{uuid.uuid4().hex}.jpg")
                img.save(img_path)
                image_paths.append(img_path)

        # Load scope items for AI
        scope_items = load_scope_for_project(project_id)

        data = {
            "project_id": project_id,
            "project_name": project_name,
            "client_name": client_name,
            "location": location,
            "date": date,
            "weather": weather,
            "work_done": work_done,
            "safety_notes": safety_notes,
        }

        ai_analysis = analyze_scope_vs_log(scope_items, data) if enable_ai else None

        filename = f"log_{uuid.uuid4().hex[:8]}.pdf"
        save_path = os.path.join(GENERATED_FOLDER, filename)

        create_daily_log_pdf(
            data=data,
            image_paths=image_paths,
            logo_path=logo_path,
            ai_analysis=ai_analysis,
            progress_report=None,
            save_path=save_path,
            weather_icon_path=None,
            safety_sheet_path=safety_path,
        )

        return jsonify({"pdf_url": f"/generated/{filename}"}), 200

    except Exception as e:
        return jsonify({"error": f"Server error in form upload: {str(e)}"}), 500

@app.route("/form")
def form():
    return render_template("form.html")
