from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.ai_utils import analyze_images
from utils.scope_utils import analyze_scope_progress
from utils.weather import get_weather_icon_path
from docx import Document

app = Flask(__name__)

# ---- Configuration ----
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['COMPRESSED_FOLDER'] = 'static/compressed'
app.config['GENERATED_FOLDER'] = 'static/generated'
app.config['SCOPE_FOLDER'] = 'static/scope_docs'
app.config['LOGO_FOLDER'] = 'static/logos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx', 'txt'}

# ---- Ensure folders exist ----
for folder in [
    app.config['UPLOAD_FOLDER'],
    app.config['COMPRESSED_FOLDER'],
    app.config['GENERATED_FOLDER'],
    app.config['SCOPE_FOLDER'],
    app.config['LOGO_FOLDER']
]:
    os.makedirs(folder, exist_ok=True)

# ---- Helper ----
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---- Routes ----

@app.route('/')
def index():
    return '✅ Nails & Notes API is running!'

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/get_weather', methods=['POST'])
def get_weather():
    location = request.form['location']
    weather = os.popen(f"curl -s 'https://wttr.in/{location}?format=3'").read().strip()
    return jsonify({'weather': weather})

@app.route('/generated/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

@app.route('/generate_form', methods=['POST'])
def generate_form():
    data = request.form.to_dict()
    files = request.files

    # ---- Save job site images ----
    image_paths = []
    for file in files.getlist("images"):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            image_paths.append(path)

    # ---- Save logo ----
    logo_path = None
    logo_file = files.get('logo')
    if logo_file and allowed_file(logo_file.filename):
        logo_filename = secure_filename(logo_file.filename)
        logo_path = os.path.join(app.config['LOGO_FOLDER'], logo_filename)
        logo_file.save(logo_path)

    # ---- Save safety sheet ----
    safety_path = None
    safety_file = files.get('safety_sheet')
    if safety_file and allowed_file(safety_file.filename):
        safety_filename = secure_filename(safety_file.filename)
        safety_path = os.path.join(app.config['UPLOAD_FOLDER'], safety_filename)
        safety_file.save(safety_path)

    # ---- Save and read scope doc ----
    scope_text = ""
    scope_file = files.get('scope_doc')
    if scope_file and allowed_file(scope_file.filename):
        scope_filename = secure_filename(scope_file.filename)
        scope_path = os.path.join(app.config['SCOPE_FOLDER'], scope_filename)
        scope_file.save(scope_path)

        ext = os.path.splitext(scope_path)[1].lower()
        if ext == ".docx":
            doc = Document(scope_path)
            scope_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        elif ext == ".txt":
            with open(scope_path, "r") as f:
                scope_text = f.read()

    # ---- Weather Icon ----
    weather_desc = data.get("weather", "")
    weather_icon_path = get_weather_icon_path(weather_desc)

    # ---- AI Analysis ----
    ai_analysis = ""
    progress_report = ""
    if data.get('enable_ai') == 'on':
        ai_analysis = analyze_images(image_paths)
        if scope_text:
            combined_log = " ".join([
                data.get("crew_notes", ""),
                data.get("work_done", ""),
                data.get("safety_notes", "")
            ])
            progress_report = analyze_scope_progress(scope_text, combined_log)

    # ---- Generate PDF ----
    pdf_filename = f"Log_{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
    create_daily_log_pdf(
        data,
        image_paths,
        logo_path=logo_path,
        ai_analysis=ai_analysis,
        progress_report=progress_report,
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_path
    )

    return jsonify({'pdf_url': f"/generated/{pdf_filename}"})

if __name__ == '__main__':
    app.run(debug=True)
