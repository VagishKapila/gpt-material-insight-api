from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log, load_scope_for_project
import os, uuid, fitz, docx
import pandas as pd

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "scope"
TEMP_DATA = {}  # In-memory preview state

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def index():
    return "✅ Daily Log AI is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_from_form():
    try:
        form = request.form
        files = request.files

        project_name = form.get("project_name", "")
        project_id = project_name.replace(" ", "_").lower()
        data = {
            "project_id": project_id,
            "project_name": project_name,
            "client_name": form.get("client_name", ""),
            "location": form.get("location", ""),
            "date": form.get("date", ""),
            "weather": form.get("weather", ""),
            "work_done": form.get("work_done", ""),
            "safety_notes": form.get("safety_notes", ""),
            "crew_notes": form.get("crew_notes", ""),
        }

        # --- Handle Scope Upload ---
        scope_file = files.get("scope_doc")
        if scope_file and scope_file.filename:
            ext = os.path.splitext(scope_file.filename)[1].lower()
            extracted = ""
            if ext == ".pdf":
                with fitz.open(stream=scope_file.stream.read(), filetype="pdf") as doc:
                    extracted = "\n".join(page.get_text() for page in doc)
            elif ext == ".docx":
                extracted = "\n".join(p.text for p in docx.Document(scope_file).paragraphs)
            elif ext == ".txt":
                extracted = scope_file.read().decode("utf-8")
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(scope_file)
                extracted = "\n".join(df.astype(str).apply(" ".join, axis=1))
            with open(os.path.join(SCOPE_FOLDER, f"scope_{project_id}.txt"), "w", encoding="utf-8") as f:
                f.write(extracted)

        # --- Handle File Uploads ---
        logo_file = files.get("logo")
        logo_path = None
        if logo_file and logo_file.filename:
            logo_path = os.path.join(UPLOAD_FOLDER, f"logo_{uuid.uuid4().hex}.png")
            logo_file.save(logo_path)

        safety_file = files.get("safety_sheet")
        safety_path = None
        if safety_file and safety_file.filename:
            safety_path = os.path.join(UPLOAD_FOLDER, f"safety_{uuid.uuid4().hex}.pdf")
            safety_file.save(safety_path)

        image_paths = []
        for img in request.files.getlist("images"):
            if img and img.filename:
                path = os.path.join(UPLOAD_FOLDER, f"img_{uuid.uuid4().hex}.jpg")
                img.save(path)
                image_paths.append(path)

        # --- AI Analysis ---
        scope_items = load_scope_for_project(project_id)
        ai_analysis = analyze_scope_vs_log(scope_items, data) if form.get("enable_ai") == "on" else None

        # Save temp preview state
        session_id = uuid.uuid4().hex[:8]
        TEMP_DATA[session_id] = {
            "data": data,
            "ai_analysis": ai_analysis,
            "images": image_paths,
            "logo": logo_path,
            "safety": safety_path
        }

        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        return jsonify({"error": f"Form error: {str(e)}"}), 500

@app.route("/preview/<session_id>")
def preview(session_id):
    context = TEMP_DATA.get(session_id)
    if not context:
        return "Session expired or not found.", 404
    return render_template("preview.html", session_id=session_id, **context)

@app.route("/finalize_preview", methods=["POST"])
def finalize_preview():
    try:
        session_id = request.form.get("session_id")
        context = TEMP_DATA.get(session_id)
        if not context:
            return "Session expired.", 400

        # Accept updated confidence scores from user edits
        edited_scores = {}
        for k, v in request.form.items():
            if k.startswith("score_"):
                item = k.replace("score_", "")
                try:
                    edited_scores[item] = float(v)
                except:
                    continue

        for s in context["ai_analysis"]["scored_items"]:
            item = s["scope"][:75]
            if item in edited_scores:
                s["confidence"] = round(edited_scores[item])
                s["match"] = s["confidence"] >= 65

        filename = f"log_{uuid.uuid4().hex[:8]}.pdf"
        path = os.path.join(GENERATED_FOLDER, filename)

        create_daily_log_pdf(
            data=context["data"],
            image_paths=context["images"],
            logo_path=context["logo"],
            ai_analysis=context["ai_analysis"],
            progress_report=None,
            save_path=path,
            weather_icon_path=None,
            safety_sheet_path=context["safety"]
        )

        del TEMP_DATA[session_id]
        return redirect(f"/generated/{filename}")

    except Exception as e:
        return f"Error finalizing: {str(e)}", 500

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

@app.route("/upload_ui")
def upload_ui():
    return render_template("react_uploader.html")
