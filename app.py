from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename
import os
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_PDF_FOLDER'] = 'static/generated'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB upload limit

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_PDF_FOLDER'], exist_ok=True)

@app.route('/')
def home():
    return "✅ Nails & Notes AI: Daily Log PDF Generator is running!"

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        images = request.files.getlist('photos')
        image_paths = []

        for image in images:
            if image.filename != '':
                filename = secure_filename(image.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Save in chunks to avoid memory spikes
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = image.stream.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)

                image_paths.append(save_path)

        form_data['photos'] = image_paths
        pdf_path = create_daily_log_pdf(form_data, app.config['GENERATED_PDF_FOLDER'])
        return send_file(pdf_path, as_attachment=True)

    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
