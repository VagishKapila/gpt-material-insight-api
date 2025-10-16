from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from utils.pdf_generator import create_daily_log_pdf  # Make sure this exists

app = Flask(__name__)

# Folder configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_PDF_FOLDER'] = 'generated_pdfs'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_PDF_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return "✅ Nails & Notes Daily Log App is Running"

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Capture form data
        form_data = request.form.to_dict()

        # Save uploaded images
        images = request.files.getlist('photos')
        image_paths = []
        for image in images:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                image_paths.append(filepath)

        # Add image paths to form_data
        form_data['photos'] = image_paths

        # Generate PDF
        pdf_path = create_daily_log_pdf(form_data, app.config['GENERATED_PDF_FOLDER'])

        return send_file(pdf_path, as_attachment=True)

    # GET request: show form
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
