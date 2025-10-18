from flask import Flask, request, render_template, send_file, redirect, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import requests
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

@app.route("/")
def home():
    return "Server is running!"

@app.route("/form", methods=["GET"])
def show_form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return jsonify({"error": "No location provided"}), 400

    try:
        response = requests.get(f"https://wttr.in/{location}?format=1", timeout=3)
        weather = response.text.strip()
        return jsonify({"weather": weather})
    except Exception as e:
        print(f"[Weather API Error] {e}")
        return jsonify({"error": "Unable to fetch weather"}), 500

@app.route("/submit", methods=["POST"])
def submit_log():
    try:
        form = request.form
        files = request.files.getlist("photos")
        logo_file = request.files.get("logo")

        saved_files = []
        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(filepath)
                saved_files.append(filepath)

        logo_path = None
        if logo_file and logo_file.filename:
            logo_name = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_name)
            logo_file.save(logo_path)

        # Determine which weather to use
        weather = form.get("weather_override") or form.get("weather")

        data = {
            "date": form.get("date"),
            "project_name": form.get("project_name"),
            "client_name": form.get("client_name"),
            "job_number": form.get("job_number"),
            "prepared_by": form.get("prepared_by"),
            "location": form.get("location"),
            "gc_or_sub": form.get("gc_or_sub"),
            "crew_notes": form.get("crew_notes"),
            "work_done": form.get("work_done"),
            "deliveries": form.get("deliveries"),
            "inspections": form.get("inspections"),
            "equipment_used": form.get("equipment_used"),
            "safety_notes": form.get("safety_notes"),
            "weather": weather,
            "notes": form.get("notes"),
            "photos": saved_files,
            "logo_path": logo_path,
            "include_page_2": "include_page_2" in form
        }

        output_dir = tempfile.mkdtemp()
        pdf_path = create_daily_log_pdf(data, output_dir)
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"[Server Error] {e}")
        return "Error occurred while submitting the log.", 500

if __name__ == "__main__":
    app.run(debug=True)
