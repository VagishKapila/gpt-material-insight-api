import os
import json
import uuid
from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log
from PyPDF2 import PdfReader

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
SCOPE_FOLDER = 'static/scope'

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def home():
    return "Nails & Notes: Daily Log AI"

@app.route('/form')
def form():
    return render_template('form.html')

def extract_scope_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    lines = [line.strip() for line in text.splitlines() if len(line.strip().split()) >= 5]
    return lines

@app.route('/generate_form', methods=['POST'])
def generate_form():
    data = dict(request.form)
    project_id = data.get("project_name", "default_project").strip().replace(" ", "_").lower()

    # Save Scope of Work PDF if uploaded (only once per project)
    scope_file = request.files.get("scope_doc")
    scope_path = f"{SCOPE_FOLDER}/{project_id}_scope.json"
    if scope_file and not os.path.exists(scope_path):
        scope_pdf_path = os.path.join(SCOPE_FOLDER, secure_filename(scope_file.filename))
        scope_file.save(scope_pdf_path)
        extracted_scope = extract_scope_from_pdf(scope_pdf_path)
        with open(scope_path, "w") as f:
            json.dump(extracted_scope, f, indent=2)

    # Load saved scope for this project
    try:
        with open(scope_path, "r") as f:
            saved_scope = json.load(f)
    except:
        saved_scope = []

    # Get Daily Log inputs
    work_done = data.get("work_done", "")
    safety_notes = data.get("safety_notes", "")
    crew_notes = data.get("crew_notes", "")

    # Run comparison AI
    comparison_result = analyze_scope_vs_log(saved_scope, work_done, crew_notes, safety_notes)

    # Save daily log as PDF
    filename = f"daily_log_{uuid.uuid4().hex[:8]}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, filename)
    create_daily_log_pdf(data, [], None, True, comparison_result, save_path)

    return f"Generated: <a href='/generated/{filename}'>{filename}</a>"

@app.route('/generated/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)
