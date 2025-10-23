import os
import uuid
from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.scope_utils import analyze_scope_progress, extract_scope_text
from utils.ai_utils import analyze_images
import requests
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'
app.config['AUTOFILL_FOLDER'] = 'static/autofill'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUTOFILL_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return "Daily Log Generator is running!"

@app.route('/form', methods=['GET'])
def form():
    try:
        with open(os.path.join(app.config['AUTOFILL_FOLDER'], 'last_data.json'), 'r') as f:
            last_data = json.load(f)
    except:
        last_data = {}
    return render_template('form.html', last_data=last_data)

@app.route('/get_weather', methods=['GET'])
def get_weather():
    location = request.args.get('location', '')
    try:
        res = requests.get(f'https://wttr.in/{location}?format=3')
        return res.text
    except:
        return "Weather unavailable"

@app.route('/generate_form', methods=['POST'])
def generate_form():
    data = request.form.to_dict()
    files = request.files
    image_paths = []

    # Handle job site images
    for file_key in files:
        if 'images' in file_key:
            file = files[file_key]
            if file.filename:
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                image_paths.append(path)

    # Handle uploaded logo
    logo_path = None
    if 'logo' in files and files['logo'].filename:
        logo_file = files['logo']
        logo_filename = f"{uuid.uuid4().hex}_{secure_filename(logo_file.filename)}"
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        logo_file.save(logo_path)

    # Handle safety sheet upload
    safety_path = None
    if 'safety_file' in files and files['safety_file'].filename:
        safety_file = files['safety_file']
        safety_filename = f"{uuid.uuid4().hex}_{secure_filename(safety_file.filename)}"
        safety_path = os.path.join(app.config['UPLOAD_FOLDER'], safety_filename)
        safety_file.save(safety_path)

    # Save last form inputs (except files)
    with open(os.path.join(app.config['AUTOFILL_FOLDER'], 'last_data.json'), 'w') as f:
        json.dump(data, f)

    # Extract & analyze scope document
    scope_text = ""
    if 'scope_doc' in files and files['scope_doc'].filename:
        scope_file = files['scope_doc']
        scope_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4().hex}_{secure_filename(scope_file.filename)}")
        scope_file.save(scope_path)
        scope_text = extract_scope_text(scope_path)

    # Analyze AI
    ai_analysis = ""
    progress_report = ""
    if data.get('enable_ai') == 'on':
    ai_analysis = analyze_images(image_paths)
    if scope_text:
        # Combine log notes for comparison
        log_text = " ".join([
            data.get("crew_notes", ""),
            data.get("work_done", ""),
            data.get("safety_notes", "")
        ])
        progress_report = analyze_scope_progress(scope_text, log_text)

    # Generate PDF
    pdf_filename = f"Log_{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
    create_daily_log_pdf(data, image_paths, logo_path=logo_path, ai_analysis=ai_analysis, scope_progress=progress_report, save_path=save_path, safety_path=safety_path)

    return jsonify({'pdf_url': f"/generated/{pdf_filename}"})

@app.route('/generated/<filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)
