from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.image_compression import compress_and_rotate_image, clean_temp_images
from utils.data_storage import load_last_project_data, save_project_data
import os
import datetime
import requests
import uuid

app = Flask(__name__)

# Folder paths
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

@app.route('/')
def health():
    return "App is running"

@app.route('/form')
def form():
    project_name = request.args.get("project", "").strip().lower().replace(" ", "_")
    last_data = load_last_project_data(project_name) if project_name else None
    return render_template('form.html', last_data=last_data or {})

@app.route('/get_weather')
def get_weather():
    location = request.args.get("location", "")
    try:
        response = requests.get(f"https://wttr.in/{location}?format=3", timeout=5)
        return jsonify({"weather": response.text.strip()})
    except Exception as e:
        return jsonify({"weather": "Could not fetch weather"})

@app.route('/generate_form', methods=['POST'])
def generate():
    try:
        form_data = request.form.to_dict(flat=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = form_data.get("project_name", "").strip()
        project_id = project_name.lower().replace(" ", "_")

        # Load last saved data
        last_data = load_last_project_data(project_id) or {}

        # Prefill missing fields from last submission
        for key in last_data:
            if not form_data.get(key):
                form_data[key] = last_data[key]

        # Save this form data for future prefill (excluding photos/weather)
        save_fields = ["project_name", "crew_notes", "work_done", "safety_notes", "equipment_used"]
        save_project_data(project_id, {k: form_data.get(k, "") for k in save_fields})

        # Upload and compress job site photos
        saved_photo_paths = []
        for photo in request.files.getlist("photos"):
            if photo and photo.filename:
                filename = secure_filename(photo.filename)
                filepath = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{uuid.uuid4().hex}_{filename}")
                photo.save(filepath)
                compressed_path = compress_and_rotate_image(filepath)
                saved_photo_paths.append(compressed_path)

        # Optional logo upload
        logo_path = None
        logo_file = request.files.get("logo")
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, f"logo_{timestamp}_{filename}")
            logo_file.save(logo_path)

        # Optional scope file
        scope_file = request.files.get("scope_file")
        if scope_file and scope_file.filename:
            filename = secure_filename(scope_file.filename)
            scope_path = os.path.join(UPLOAD_FOLDER, f"scope_{timestamp}_{filename}")
            scope_file.save(scope_path)
            print(f"🔹 Scope file uploaded: {scope_path}")

        # Weather
        weather = form_data.get("weather", "Not Provided")

        # AI/AR checkbox (default = true)
        run_ai = form_data.get("run_ai", "on").lower() in ["on", "true", "yes", "1"]

        # Generate PDF
        output_pdf_path = os.path.join(GENERATED_FOLDER, f"DailyLog_{project_id}_{timestamp}.pdf")
        create_daily_log_pdf(
            form_data=form_data,
            photo_paths=saved_photo_paths,
            output_path=output_pdf_path,
            logo_path=logo_path,
            weather=weather,
            enable_ai_analysis=run_ai
        )

        clean_temp_images()

        return jsonify({"pdf_url": f"/generated/{os.path.basename(output_pdf_path)}"})

    except Exception as e:
        print("❌ Error in /generate_form:", str(e))
        return "Internal Server Error", 500

@app.route('/generated/<filename>')
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
