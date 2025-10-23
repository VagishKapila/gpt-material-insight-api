from flask import Flask, request, render_template, send_from_directory, session
from werkzeug.utils import secure_filename
import os
import uuid
import datetime
import json
from utils.pdf_generator import create_daily_log_pdf
from ai_scope_tracking import (
    extract_scope_text,
    extract_scope_tasks,
    save_project_scope,
    load_project_scope,
    compare_scope_to_daily_log,
    format_progress_report
)

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'
app.config['AUTOFILL_FOLDER'] = 'static/autofill'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUTOFILL_FOLDER'], exist_ok=True)

def get_autofill_path(project_id):
    return os.path.join(app.config['AUTOFILL_FOLDER'], f"{project_id}.json")

def save_autofill(project_id, data):
    path = get_autofill_path(project_id)
    with open(path, 'w') as f:
        json.dump(data, f)

def load_autofill(project_id):
    path = get_autofill_path(project_id)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    return 'Nails & Notes Daily Log System is running'

@app.route('/form', methods=['GET'])
def form():
    project_name = request.args.get('project_name', '').strip()
    project_id = project_name.lower().replace(" ", "_") if project_name else ""
    last_data = load_autofill(project_id) if project_id else {}
    return render_template('form.html', last_data=last_data)

@app.route('/get_weather', methods=['GET'])
def get_weather():
    import requests
    try:
        res = requests.get('https://wttr.in?format=3')
        return res.text
    except:
        return "Weather unavailable"

@app.route('/generate_form', methods=['POST'])
def generate_form():
    data = request.form.to_dict()
    project_name = data.get('project_name', '').strip()
    project_id = project_name.lower().replace(" ", "_")
    work_done = data.get('work_done', '')
    include_ai = data.get('enable_ai') == 'on'

    # Handle images
    images = request.files.getlist('images')
    image_paths = []
    for img in images:
        if img.filename:
            filename = f"{uuid.uuid4().hex}_{secure_filename(img.filename)}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(path)
            image_paths.append(path)

    # Handle logo
    logo_path = None
    if 'logo' in request.files and request.files['logo'].filename:
        logo_file = request.files['logo']
        logo_filename = f"{uuid.uuid4().hex}_{secure_filename(logo_file.filename)}"
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        logo_file.save(logo_path)

    # Handle scope
    scope_path = None
    if 'scope_doc' in request.files and request.files['scope_doc'].filename:
        scope_file = request.files['scope_doc']
        scope_filename = f"{uuid.uuid4().hex}_{secure_filename(scope_file.filename)}"
        scope_path = os.path.join(app.config['UPLOAD_FOLDER'], scope_filename)
        scope_file.save(scope_path)

        scope_text = extract_scope_text(scope_path)
        scope_tasks = extract_scope_tasks(scope_text)
        save_project_scope(project_id, scope_tasks)

    scope_tasks = load_project_scope(project_id)
    progress_report = ""
    if scope_tasks:
        progress_result = compare_scope_to_daily_log(scope_tasks, work_done)
        progress_report = format_progress_report(progress_result)

    # Save autofill fields
    save_autofill(project_id, {
        'project_name': project_name,
        'location': data.get('location', ''),
        'crew_notes': data.get('crew_notes', ''),
        'work_done': data.get('work_done', ''),
        'safety_notes': data.get('safety_notes', ''),
        'weather': data.get('weather', '')
    })

    # Generate PDF
    filename = f"DailyLog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    save_path = os.path.join(app.config['GENERATED_FOLDER'], filename)

    create_daily_log_pdf(
        data=data,
        image_paths=image_paths,
        logo_path=logo_path,
        save_path=save_path,
        ai_analysis=include_ai,
        progress_report=progress_report
    )

    return {"pdf_url": f"/generated/{filename}"}

@app.route('/generated/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)
