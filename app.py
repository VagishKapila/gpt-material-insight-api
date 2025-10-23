from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.image_compression import compress_and_rotate_image, clean_temp_images
import os
import datetime
import uuid
import requests

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# Prefill memory cache (in-memory only)
PROJECT_CACHE = {}

@app.route('/')
def health_check():
    return "✅ Nails & Notes: Daily Log AI is running!"

@app.route('/form')
def form():
    project_id = request.args.get("project", "").strip().lower().replace(" ", "_")
    last_data = PROJECT_CACHE.get(project_id, {}) if project_id else {}
    return render_template('form.html', last_data=last_data)

@app.route('/get_weather')
def get_weather():
    location = request.args.get("location", "")
    try:
        res = requests.get(f"https://wttr.in/{location}?format=3", timeout=5)
        return jsonify({"weather": res.text.strip()})
    except:
        return jsonify({"weather": "Could not fetch weather"})

@app.route('/generate_form', methods=['POST'])
def generate_form():
    try:
        form = request.form.to_dict()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        project_id = form.get("project_name", "").strip().lower().replace(" ", "_")

        # Restore prior form data
        if project_id in PROJECT_CACHE:
            for k, v in PROJECT_CACHE[project_id].items():
                if not form.get(k):
                    form[k] = v

        # Save current data (excluding dynamic fields)
        reusable_fields = [
            "project_name", "client_name", "location", "job_number", "gc_name",
            "crew_notes", "work_done", "safety_notes", "equipment_used"
        ]
        PROJECT_CACHE[project_id] = {k: form.get(k, "") for k in reusable_fields}

        # Save & compress job site photos
        saved_photo_paths = []
        for file in request.files.getlist("images"):
            if file.filename:
                fname = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{uuid.uuid4().hex}_{fname}")
                file.save(path)
                saved_photo_paths.append(compress_and_rotate_image(path))

        # Save logo
        logo = request.files.get("logo")
        logo_path = None
        if logo and logo.filename:
            fname = secure_filename(logo.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, f"logo_{timestamp}_{fname}")
            logo.save(logo_path)

        # Determine AI checkbox
        enable_ai = form.get("run_ai", "on").lower() in ["on", "true", "yes", "1"]

        # Final PDF output
        output_path = os.path.join(GENERATED_FOLDER, f"DailyLog_{timestamp}.pdf")
        create_daily_log_pdf(
            form_data=form,
            photo_paths=saved_photo_paths,
            output_path=output_path,
            logo_path=logo_path,
            weather=form.get("weather", ""),
            enable_ai_analysis=enable_ai
        )

        clean_temp_images()
        return jsonify({"pdf_url": f"/generated/{os.path.basename(output_path)}"})

    except Exception as e:
        print("🔥 ERROR generating log:", e)
        return "Internal Server Error", 500

@app.route('/generated/<filename>')
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
