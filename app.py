from flask import Flask, request, render_template, send_from_directory, jsonify
from utils.pdf_generator import create_daily_log_pdf
import os
import uuid
import requests
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'
app.config['AUTOFILL_FOLDER'] = 'static/autofill'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['AUTOFILL_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return 'Nails & Notes API is running.'

@app.route('/form', methods=['GET'])
def form():
    return render_template('form.html')

@app.route('/get_weather', methods=['GET'])
def get_weather():
    location = request.args.get('location', '')
    try:
        response = requests.get(f'https://wttr.in/{location}?format=j1', timeout=5)
        weather_data = response.json()
        current = weather_data['current_condition'][0]
        temp = f"{current['temp_C']}°C"
        icon_url = current['weatherIconUrl'][0]['value']
        return jsonify({'temp': temp, 'icon_url': icon_url})
    except Exception as e:
        return jsonify({'temp': 'N/A', 'icon_url': ''})

@app.route('/generate_form', methods=['POST'])
def generate_form():
    data = request.form.to_dict()
    ai_analysis = 'enable_ai' in data
    project_id = data.get('project_name', 'default_project').replace(" ", "_")

    # Save image uploads
    image_paths = []
    for uploaded_file in request.files.getlist("images"):
        if uploaded_file.filename != "":
            filename = secure_filename(str(uuid.uuid4()) + "_" + uploaded_file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(path)
            image_paths.append(path)

    # Save safety sheet if uploaded
    safety_sheet_path = None
    safety_file = request.files.get("safety_sheet")
    if safety_file and safety_file.filename != "":
        filename = secure_filename(str(uuid.uuid4()) + "_" + safety_file.filename)
        safety_sheet_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        safety_file.save(safety_sheet_path)

    # Save project scope if uploaded
    scope_doc_path = None
    scope_file = request.files.get("scope_doc")
    if scope_file and scope_file.filename != "":
        filename = secure_filename(str(uuid.uuid4()) + "_" + scope_file.filename)
        scope_doc_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        scope_file.save(scope_doc_path)
        # Save path for future auto-fill
        with open(f"{app.config['AUTOFILL_FOLDER']}/{project_id}_scope_path.json", 'w') as f:
            json.dump({'scope_doc_path': scope_doc_path}, f)
    else:
        # Load existing scope path
        try:
            with open(f"{app.config['AUTOFILL_FOLDER']}/{project_id}_scope_path.json", 'r') as f:
                scope_doc_path = json.load(f).get('scope_doc_path')
        except:
            scope_doc_path = None

    # Save project autofill data
    with open(f"{app.config['AUTOFILL_FOLDER']}/{project_id}_last_data.json", 'w') as f:
        json.dump(data, f)

    # Save logo
    logo_path = None
    logo_file = request.files.get("logo")
    if logo_file and logo_file.filename != "":
        filename = secure_filename(str(uuid.uuid4()) + "_" + logo_file.filename)
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logo_file.save(logo_path)

    # Save weather icon
    weather_icon_path = None
    weather_icon_url = data.get("weather_icon_url", "")
    if weather_icon_url:
        try:
            icon_response = requests.get(weather_icon_url)
            if icon_response.status_code == 200:
                weather_icon_filename = f"weather_icon_{project_id}_{uuid.uuid4()}.png"
                weather_icon_path = os.path.join(app.config['UPLOAD_FOLDER'], weather_icon_filename)
                with open(weather_icon_path, 'wb') as f:
                    f.write(icon_response.content)
        except:
            pass

    # Save PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Daily_Log_{project_id}_{timestamp}.pdf"
    save_path = os.path.join(app.config['GENERATED_FOLDER'], filename)

    # Generate PDF
    create_daily_log_pdf(
        data=data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=ai_analysis,
        progress_report=scope_doc_path,
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_sheet_path
    )

    return jsonify({'pdf_url': f'/generated/{filename}'})

@app.route('/generated/<filename>', methods=['GET'])
def serve_pdf(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)
