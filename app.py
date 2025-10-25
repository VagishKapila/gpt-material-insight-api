from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
import datetime
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import compare_scope_with_log

app = Flask(__name__)

# Configure paths
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
SCOPE_FOLDER = 'static/scopes'
DEBUG_FOLDER = 'static/debug_output'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['SCOPE_FOLDER'] = SCOPE_FOLDER

# Ensure folders exist
for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER, DEBUG_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def home():
    return 'Nails & Notes Daily Log API is running.'

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/generate_form', methods=['POST'])
def generate_form():
    try:
        # Get form fields
        project_name = request.form.get('project_name')
        client_name = request.form.get('client_name')
        location = request.form.get('location')
        date = request.form.get('date') or str(datetime.date.today())
        weather = request.form.get('weather')
        crew_notes = request.form.get('crew_notes')
        work_done = request.form.get('work_done')
        safety_notes = request.form.get('safety_notes')
        enable_ai = 'enable_ai' in request.form

        # Save uploaded files
        def save_file(field, subfolder):
            file = request.files.get(field)
            if file and file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
                os.makedirs(path, exist_ok=True)
                full_path = os.path.join(path, filename)
                file.save(full_path)
                return full_path
            return None

        logo_path = save_file('logo', 'logos')
        safety_sheet_path = save_file('safety_sheet', 'safety')
        scope_path = save_file('scope_doc', 'scopes')

        # Save multiple images
        image_paths = []
        images = request.files.getlist('images')
        for img in images:
            if img.filename:
                img_filename = secure_filename(img.filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'photos', img_filename)
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img.save(img_path)
                image_paths.append(img_path)

        # Build data dict
        data = {
            'project_name': project_name,
            'client_name': client_name,
            'location': location,
            'date': date,
            'weather': weather,
            'crew_notes': crew_notes,
            'work_done': work_done,
            'safety_notes': safety_notes,
        }

        # AI scope analysis
        progress_report = None
        if enable_ai and scope_path:
            try:
                scope_json_path = scope_path.replace('.txt', '.json')
                with open(scope_path, 'r') as f:
                    scope_items = [line.strip() for line in f.readlines() if line.strip()]
                with open(scope_json_path, 'w') as f:
                    import json
                    json.dump(scope_items, f, indent=2)
                daily_log_text = f"{crew_notes}\n{work_done}\n{safety_notes}"
                progress_report = compare_scope_with_log(scope_json_path, daily_log_text)
            except Exception as e:
                print(f"Error in AI scope analysis: {e}")

        # Create PDF
        filename = f"DailyLog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        save_path = os.path.join(app.config['GENERATED_FOLDER'], filename)

        create_daily_log_pdf(
            data=data,
            image_paths=image_paths,
            logo_path=logo_path,
            ai_analysis=enable_ai,
            progress_report=progress_report,
            save_path=save_path,
            weather_icon_path=None,
            safety_sheet_path=safety_sheet_path
        )

        return f"PDF generated: <a href='/generated/{filename}' target='_blank'>{filename}</a>"

    except Exception as e:
        return f"❌ Error: {e}"

@app.route('/generated/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
