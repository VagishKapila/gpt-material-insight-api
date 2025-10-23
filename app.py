from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid
from utils.pdf_generator import create_daily_log_pdf
from ai_scope_tracking import extract_scope_text, extract_scope_tasks, save_project_scope, load_project_scope, compare_scope_to_daily_log, format_progress_report
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/generated', exist_ok=True)

@app.route('/')
def index():
    return 'Nails & Notes Daily Log System is running'

@app.route('/form', methods=['GET'])
def form():
    return render_template('form.html')

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
    include_ai = data.get('include_ai') == 'on'

    # Handle image uploads
    images = request.files.getlist('photos')
    image_paths = []
    for img in images:
        if img.filename:
            filename = f"{uuid.uuid4().hex}_{secure_filename(img.filename)}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(img_path)
            image_paths.append(img_path)

    # Handle logo
    logo_path = None
    if 'logo' in request.files and request.files['logo'].filename:
        logo_file = request.files['logo']
        logo_filename = f"{uuid.uuid4().hex}_{secure_filename(logo_file.filename)}"
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        logo_file.save(logo_path)

    # Handle Scope Upload
    scope_path = None
    if 'scope_file' in request.files and request.files['scope_file'].filename:
        scope_file = request.files['scope_file']
        scope_filename = f"{uuid.uuid4().hex}_{secure_filename(scope_file.filename)}"
        scope_path = os.path.join(app.config['UPLOAD_FOLDER'], scope_filename)
        scope_file.save(scope_path)

        # Extract and save tasks if first upload
        scope_text = extract_scope_text(scope_path)
        scope_tasks = extract_scope_tasks(scope_text)
        save_project_scope(project_id, scope_tasks)

    # Load existing scope
    scope_tasks = load_project_scope(project_id)
    progress_report = ""
    if scope_tasks:
        progress_result = compare_scope_to_daily_log(scope_tasks, work_done)
        progress_report = format_progress_report(progress_result)

    # Generate filename and call PDF generator
    filename = f"DailyLog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    save_path = os.path.join("static/generated", filename)

    create_daily_log_pdf(data=data,
                         image_paths=image_paths,
                         logo_path=logo_path,
                         save_path=save_path,
                         ai_analysis=include_ai,
                         progress_report=progress_report)

    return {"pdf_url": f"/generated/{filename}"}

@app.route('/generated/<filename>')
def serve_file(filename):
    return send_from_directory('static/generated', filename)
