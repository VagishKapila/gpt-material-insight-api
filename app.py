from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
import os
import datetime
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

@app.route('/')
def health():
    return "App is running"

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/get_weather')
def get_weather():
    location = request.args.get("location", "")
    try:
        response = requests.get(f"https://wttr.in/{location}?format=3")
        return jsonify({"weather": response.text.strip()})
    except Exception as e:
        return jsonify({"weather": "Could not fetch weather"})

@app.route('/generate_form', methods=['POST'])
def generate():
    try:
        data = request.form

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        photos = request.files.getlist('photos')
        logo = request.files.get('logo')
        scope_file = request.files.get('scope_file')

        saved_photo_paths = []
        for photo in photos:
            if photo.filename:
                filename = secure_filename(photo.filename)
                path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{filename}")
                photo.save(path)
                saved_photo_paths.append(path)

        logo_path = None
        if logo and logo.filename:
            filename = secure_filename(logo.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, f"logo_{timestamp}_{filename}")
            logo.save(logo_path)

        if scope_file and scope_file.filename:
            filename = secure_filename(scope_file.filename)
            scope_path = os.path.join(UPLOAD_FOLDER, f"scope_{timestamp}_{filename}")
            scope_file.save(scope_path)
            print(f"Scope of Work file saved to: {scope_path}")

        output_pdf = os.path.join(GENERATED_FOLDER, f"DailyLog_{timestamp}.pdf")
        create_daily_log_pdf(data, saved_photo_paths, output_pdf, logo_path)

        return jsonify({"pdf_url": f"/generated/{os.path.basename(output_pdf)}"})

    except Exception as e:
        print("Error in /generate_form:", e)
        return "Internal Server Error", 500

@app.route('/generated/<filename>')
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
