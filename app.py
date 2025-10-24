# app.py
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import os
import uuid
from image_utils import preprocess_images
from pdf_generator import create_daily_log_pdf

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

@app.route('/')
def health_check():
    return "✅ Daily Log AI is running."

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/generate_form', methods=['POST'])
def generate_form():
    try:
        # Collect data
        data = {key: request.form.get(key, '') for key in request.form}

        # Handle uploads
        image_files = request.files.getlist('images')
        logo_file = request.files.get('logo')
        safety_file = request.files.get('safety_sheet')

        image_paths, logo_path, safety_path = [], None, None

        for img in image_files:
            filename = secure_filename(img.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            img.save(path)
            image_paths.append(path)

        if logo_file:
            logo_filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, logo_filename)
            logo_file.save(logo_path)

        if safety_file:
            safety_filename = secure_filename(safety_file.filename)
            safety_path = os.path.join(UPLOAD_FOLDER, safety_filename)
            safety_file.save(safety_path)

        # Preprocess image uploads
        image_paths = preprocess_images(image_paths)
        if logo_path:
            logo_path = preprocess_images([logo_path])[0]
        if safety_path and safety_path.endswith(('.jpg', '.jpeg', '.png')):
            safety_path = preprocess_images([safety_path])[0]

        # Generate PDF
        pdf_filename = f"log_{uuid.uuid4().hex}.pdf"
        output_path = os.path.join(GENERATED_FOLDER, pdf_filename)

        create_daily_log_pdf(
            data=data,
            image_paths=image_paths,
            output_path=output_path,
            logo_path=logo_path,
            ai_analysis=data.get('ai_analysis'),
            progress_report=data.get('progress_report'),
            safety_path=safety_path
        )

        return jsonify({"pdf_url": f"/generated/{pdf_filename}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generated/<filename>')
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
