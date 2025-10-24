import os
import time
from flask import Flask, request, render_template, send_from_directory, jsonify
from utils.pdf_generator import create_daily_log_pdf
from utils.image_utils import preprocess_images
from werkzeug.utils import secure_filename
from datetime import datetime
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
AUTOFILL_FOLDER = 'static/autofill'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx', 'doc'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER

# 🧾 Debug Print - Confirm structure
print("🧾 Files in root:", os.listdir("."))
print("📁 Files in /utils:", os.listdir("./utils") if os.path.isdir("./utils") else "Not found")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return 'Daily Log AI - Healthy ✅'

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/get_weather', methods=['POST'])
def get_weather():
    location = request.json.get('location')
    if not location:
        return jsonify({'error': 'No location provided'}), 400

    try:
        response = requests.get(f'https://wttr.in/{location}?format=%C')
        if response.ok:
            return jsonify({'weather': response.text.strip()})
        else:
            return jsonify({'error': 'Weather fetch failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_form', methods=['POST'])
def generate_form():
    data = dict(request.form)
    project_id = data.get("project_id", "default_project")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"DailyLog_{timestamp}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, filename)

    # Upload files
    images = request.files.getlist('images')
    logo = request.files.get('logo')
    safety_sheet = request.files.get('safety_sheet')
    scope_doc = request.files.get('scope_doc')
    ai_analysis = 'enable_ai' in request.form

    image_paths = preprocess_images(images, app.config['UPLOAD_FOLDER'])
    logo_path = None
    safety_sheet_path = None
    scope_path = None

    if logo and allowed_file(logo.filename):
        logo_filename = secure_filename(logo.filename)
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        logo.save(logo_path)

    if safety_sheet and allowed_file(safety_sheet.filename):
        safety_filename = secure_filename(safety_sheet.filename)
        safety_sheet_path = os.path.join(app.config['UPLOAD_FOLDER'], safety_filename)
        safety_sheet.save(safety_sheet_path)

    if scope_doc and allowed_file(scope_doc.filename):
        scope_filename = secure_filename(scope_doc.filename)
        scope_path = os.path.join(AUTOFILL_FOLDER, f"{project_id}_scope.{scope_filename.rsplit('.', 1)[1]}")
        scope_doc.save(scope_path)

    # Check if project has previous data
    last_data_path = os.path.join(AUTOFILL_FOLDER, f"{project_id}_last.json")
    if os.path.exists(last_data_path):
        with open(last_data_path, 'r') as f:
            import json
            last_data = json.load(f)
        for key, value in last_data.items():
            data.setdefault(key, value)

    # Save new data for future autofill
    with open(last_data_path, 'w') as f:
        import json
        json.dump(data, f)

    # Get weather icon (optional)
    weather_icon_path = os.path.join("static", "icons", f"{data.get('weather', '').lower()}.png")
    if not os.path.exists(weather_icon_path):
        weather_icon_path = None

    progress_report = scope_path  # for future scope tracking

    # Slight delay for image safety
    time.sleep(1)

    try:
        create_daily_log_pdf(
            data=data,
            image_paths=image_paths,
            logo_path=logo_path,
            ai_analysis=ai_analysis,
            progress_report=progress_report,
            save_path=save_path,
            weather_icon_path=weather_icon_path,
            safety_sheet_path=safety_sheet_path
        )
    except Exception as e:
        return f"Error creating PDF: {str(e)}", 500

    return jsonify({'pdf_url': f"/generated/{filename}"})

@app.route('/generated/<filename>')
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
