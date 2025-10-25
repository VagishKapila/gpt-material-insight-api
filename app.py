from flask import Flask, render_template, request, send_from_directory, jsonify
import os, uuid, requests, json
from utils.pdf_generator import create_daily_log_pdf
from utils.scope_parser import parse_scope_file
from utils.compare_scope_vs_log import compare_scope_vs_log
from PIL import Image, ExifTags

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

def fix_image_orientation(path):
    """Rotate images correctly based on EXIF data."""
    try:
        image = Image.open(path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                image = image.rotate(180, expand=True)
            elif orientation_value == 6:
                image = image.rotate(270, expand=True)
            elif orientation_value == 8:
                image = image.rotate(90, expand=True)
        image.save(path)
    except Exception as e:
        print(f"Orientation fix failed for {path}: {e}")

@app.route('/')
def home():
    return "✅ Nails & Notes API is running."

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/generate_form', methods=['POST'])
def generate_form():
    form_data = request.form.to_dict()
    enable_ai = form_data.get('enable_ai', 'on') == 'on'

    # Handle uploads
    def save_file(file, prefix):
        if not file or file.filename == '':
            return None
        filename = f"{prefix}_{uuid.uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return path

    image_paths = []
    for file in request.files.getlist('images'):
        path = save_file(file, 'img')
        if path:
            fix_image_orientation(path)
            image_paths.append(path)

    logo_path = save_file(request.files.get('logo'), 'logo')
    safety_sheet_path = save_file(request.files.get('safety_sheet'), 'safety')
    scope_doc_path = save_file(request.files.get('scope_doc'), 'scope')

    # Weather icon (optional)
    weather_icon_path = None
    try:
        weather = form_data.get("weather", "")
        if weather:
            url = f"https://wttr.in/{weather}?format=j1"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                icon_url = res.json()["current_condition"][0]["weatherIconUrl"][0]["value"]
                icon_img = requests.get(icon_url).content
                weather_icon_path = os.path.join(UPLOAD_FOLDER, f"weather_{uuid.uuid4()}.png")
                with open(weather_icon_path, "wb") as f:
                    f.write(icon_img)
    except Exception as e:
        print(f"Weather icon fetch failed: {e}")

    # === AI Scope Comparison Logic ===
    progress_summary = None
    if enable_ai and scope_doc_path:
        try:
            parsed_scope = parse_scope_file(scope_doc_path)
            parsed_scope_path = os.path.join(UPLOAD_FOLDER, f"parsed_scope_{uuid.uuid4()}.json")
            with open(parsed_scope_path, "w") as f:
                json.dump(parsed_scope, f)

            image_captions = []  # Placeholder: Add image captioning AI later
            progress_summary = compare_scope_vs_log(
                scope_json_path=parsed_scope_path,
                crew_notes=form_data.get("crew_notes", ""),
                work_done=form_data.get("work_done", ""),
                image_captions=image_captions
            )
        except Exception as e:
            print(f"⚠️ Scope comparison failed: {e}")

    # === PDF Generation ===
    pdf_name = f"DailyLog_{uuid.uuid4()}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, pdf_name)

    create_daily_log_pdf(
        data=form_data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=enable_ai,
        progress_report=progress_summary,
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_sheet_path
    )

    return jsonify({"pdf_url": f"/generated/{pdf_name}"})

@app.route('/generated/<filename>')
def serve_generated(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
