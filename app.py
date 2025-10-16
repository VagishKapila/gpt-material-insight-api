from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_PDF_FOLDER'] = 'generated_pdfs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_PDF_FOLDER'], exist_ok=True)

# Main Form Endpoint
@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        images = request.files.getlist('photos')

        image_paths = []
        for image in images:
            if image.filename:
                filename = secure_filename(image.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(path)
                image_paths.append(path)

        form_data['photos'] = image_paths
        pdf_path = create_daily_log_pdf(form_data, app.config['GENERATED_PDF_FOLDER'])
        return send_file(pdf_path, as_attachment=True)

    return render_template('form.html')

# Health Check
@app.route('/')
def index():
    return "✅ Nails & Notes Daily Log Flask App is running."

if __name__ == '__main__':
    app.run(debug=True)
