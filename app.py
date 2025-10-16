from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Nails & Notes Daily Log API",
    description="Submit construction daily logs, upload images, and generate PDFs.",
    version="1.0.0"
)

# Optional: CORS if using frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample route
@app.get("/")
def read_root():
    return {"message": "Nails & Notes Daily Log API is live 🎯"}

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_PDF_FOLDER'] = 'generated_pdfs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_PDF_FOLDER'], exist_ok=True)

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        images = request.files.getlist('photos')
        image_paths = []
        for image in images:
            if image.filename != '':
                filename = secure_filename(image.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(path)
                image_paths.append(path)
        form_data['photos'] = image_paths
        pdf_path = create_daily_log_pdf(form_data, app.config['GENERATED_PDF_FOLDER'])
        return send_file(pdf_path, as_attachment=True)
    return render_template('form.html')

@app.route('/')
def index():
    return "Nails & Notes Daily Log App – Running"

if __name__ == '__main__':
    app.run(debug=True)
