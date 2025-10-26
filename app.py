from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import datetime
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import (
    extract_scope_items,
    analyze_scope_vs_log,
    save_scope_for_project,
    load_scope_for_project
)

app = Flask(__name__)

# Ensure folders exist
os.makedirs("static/generated", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/scope", exist_ok=True)
os.makedirs("scope_cache", exist_ok=True)

@app.route("/")
def home():
    return "✅ Nails & Notes Daily Log API is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    data = request.form.to_dict()
    project_id = data.get("project_name", "default").replace(" ", "_")

    # Handle file uploads
    images = request.files.getlist("images")
    logo = request.files.get("logo")
    safety_sheet = request.files.get("safety_sheet")
    scope_file = request.files.get("scope_doc")

    # Save images
    image_paths = []
    for image in images:
        if image:
            filename = secure_filename(image.filename)
            path = os.path.join("static/uploads", filename)
            image.save(path)
            image_paths.append(path)

    # Save logo
    logo_path = None
    if logo and logo.filename:
        filename = secure_filename(logo.filename)
        logo_path = os.path.join("static/uploads", filename)
        logo.save(logo_path)

    # Save safety sheet
    safety_sheet_path = None
    if safety_sheet and safety_sheet.filename:
        filename = secure_filename(safety_sheet.filename)
        safety_sheet_path = os.path.join("static/uploads", filename)
        safety_sheet.save(safety_sheet_path)

    # AI analysis setup
    ai_result = None
    if scope_file and scope_file.filename:
        scope_filename = secure_filename(scope_file.filename)
        scope_path = os.path.join("static/scope", scope_filename)
        scope_file.save(scope_path)

        # Extract raw text
        raw_text = ""
        if scope_path.endswith(".txt"):
            with open(scope_path, "r") as f:
                raw_text = f.read()
        elif scope_path.endswith(".docx"):
            from docx import Document
            doc = Document(scope_path)
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        elif scope_path.endswith(".pdf"):
            import fitz  # PyMuPDF
            doc = fitz.open(scope_path)
            raw_text = "\n".join([page.get_text() for page in doc])

        # Run analysis
        scope_items = extract_scope_items(raw_text)
        save_scope_for_project(project_id, scope_items)
        ai_result = analyze_scope_vs_log(
            scope_items=scope_items,
            work_done=data.get("work_done", ""),
            crew_notes=data.get("crew_notes", ""),
            safety_notes=data.get("safety_notes", "")
        )

    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"log_{timestamp}.pdf"
    save_path = os.path.join("static/generated", pdf_filename)

    # Create PDF
    create_daily_log_pdf(
        data=data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=ai_result,
        progress_report=None,
        save_path=save_path,
        safety_sheet_path=safety_sheet_path
    )

    return jsonify({"pdf_url": f"/generated/{pdf_filename}"})

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_file(os.path.join("static/generated", filename), as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True, port=8000)
