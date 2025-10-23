from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "my_secret_key")

UPLOAD_FOLDER = "static/uploads/"
GENERATED_FOLDER = "static/generated/"
SCOPE_FOLDER = "static/scope_docs/"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html"}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SCOPE_FOLDER'] = SCOPE_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(SCOPE_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_saved_scope(project_id):
    scope_path = os.path.join(SCOPE_FOLDER, f"{project_id}_scope")
    for ext in ALLOWED_EXTENSIONS:
        candidate = f"{scope_path}.{ext}"
        if os.path.exists(candidate):
            return candidate
    return None

@app.route("/")
def index():
    return "Service running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location")
    import requests
    url = f"https://wttr.in/{location}?format=%t"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.text.strip()
    except:
        pass
    return "N/A"

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        data = request.form.to_dict()
        project_id = data.get("project_id") or str(uuid.uuid4())

        # Upload scope of work if provided and doesn't already exist
        scope_file = request.files.get("scope_file")
        scope_saved_path = get_saved_scope(project_id)
        if scope_file and allowed_file(scope_file.filename) and not scope_saved_path:
            ext = secure_filename(scope_file.filename).rsplit('.', 1)[1].lower()
            scope_filename = f"{project_id}_scope.{ext}"
            scope_path = os.path.join(SCOPE_FOLDER, scope_filename)
            scope_file.save(scope_path)
            scope_saved_path = scope_path

        # Save images
        image_files = request.files.getlist("photos")
        image_paths = []
        for image in image_files:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                image.save(filepath)
                image_paths.append(filepath)

        # Logo
        logo_file = request.files.get("logo")
        logo_path = None
        if logo_file and allowed_file(logo_file.filename):
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(UPLOAD_FOLDER, filename)
            logo_file.save(logo_path)

        # PDF generation
        pdf_path = os.path.join(GENERATED_FOLDER, f"DailyLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        create_daily_log_pdf(data=data, image_paths=image_paths, pdf_path=pdf_path, logo_path=logo_path, scope_path=scope_saved_path)

        return jsonify({"pdf_url": url_for("static", filename=f"generated/{os.path.basename(pdf_path)}", _external=True)})

    except Exception as e:
        print("🔥 ERROR generating log:", str(e))
        return "Error creating log", 500

if __name__ == "__main__":
    app.run(debug=True)
