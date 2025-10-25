from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log
from utils.scope_parser import parse_scope_file
from utils.image_utils import fix_image_orientation
from utils.weather import fetch_weather_icon
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'
app.config['SCOPE_FOLDER'] = 'static/scopes'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['SCOPE_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return 'Daily Log AI – Server Running'


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/get_weather', methods=['POST'])
def get_weather():
    location = request.json.get('location')
    icon_path = fetch_weather_icon(location)
    if icon_path:
        return jsonify({'icon_url': '/' + icon_path})
    else:
        return jsonify({'error': 'Weather not found'}), 404


@app.route('/generated/<filename>')
def download_file(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)


@app.route('/generate_form', methods=['POST'])
def generate_form():
    form_data = request.form.to_dict()
    uploaded_files = request.files
    images = request.files.getlist('images')
    logo_file = request.files.get('logo')
    safety_file = request.files.get('safety_sheet')
    scope_file = request.files.get('scope_file')
    ai_analysis = form_data.get('enable_ai') == 'on'

    # Save logo
    logo_path = None
    if logo_file and logo_file.filename:
        logo_filename = secure_filename(logo_file.filename)
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{logo_filename}")
        logo_file.save(logo_path)

    # Save safety file
    safety_sheet_path = None
    if safety_file and safety_file.filename:
        safety_filename = secure_filename(safety_file.filename)
        safety_sheet_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{safety_filename}")
        safety_file.save(safety_sheet_path)

    # Save job site images
    image_paths = []
    for img in images:
        if img and img.filename:
            filename = secure_filename(img.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            img.save(save_path)
            fixed_path = fix_image_orientation(save_path)
            image_paths.append(fixed_path)

    # Scope Analysis Logic
    progress_report = None
    if ai_analysis and scope_file and scope_file.filename:
        scope_filename = secure_filename(scope_file.filename)
        scope_path = os.path.join(app.config['SCOPE_FOLDER'], f"{uuid.uuid4()}_{scope_filename}")
        scope_file.save(scope_path)

        try:
            scope_items = parse_scope_file(scope_path)
            work_text = form_data.get("work_done", "")
            progress_report = analyze_scope_vs_log(scope_items, work_text)
        except Exception as e:
            progress_report = {
                "error": f"Scope comparison failed: {str(e)}"
            }

    # Weather
    location = form_data.get("location", "")
    weather_icon_path = fetch_weather_icon(location)

    # PDF generation
    unique_filename = f"DailyLog_{uuid.uuid4().hex[:6]}.pdf"
    save_path = os.path.join(app.config['GENERATED_FOLDER'], unique_filename)

    create_daily_log_pdf(
        data=form_data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=ai_analysis,
        progress_report=progress_report,
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_sheet_path
    )

    return jsonify({'pdf_url': f'/generated/{unique_filename}'})


if __name__ == '__main__':
    app.run(debug=True)
