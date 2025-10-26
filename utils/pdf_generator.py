from flask import Flask, request, render_template, send_from_directory
import os
import uuid
from utils.compare_scope_vs_log import analyze_scope_vs_log, load_scope_for_project
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
SCOPE_FOLDER = "scope_cache"
GENERATED_FOLDER = "static/generated"
LOGO_FOLDER = "static/logos"
WEATHER_ICON_FOLDER = "static/weather"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(LOGO_FOLDER, exist_ok=True)

@app.route("/")
def health_check():
    return "✅ Daily Log AI is running."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    data = request.form.to_dict()
    files = request.files

    # Save uploaded job site images
    image_paths = []
    for i in range(1, 21):
        file_key = f"image_{i}"
        if file_key in files:
            f = files[file_key]
            if f and f.filename:
                filename = secure_filename(f.filename)
                path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
                f.save(path)
                image_paths.append(path)

    # Save logo if uploaded
    logo_path = None
    if "logo" in files and files["logo"].filename:
        logo_file = files["logo"]
        filename = secure_filename(logo_file.filename)
        logo_path = os.path.join(LOGO_FOLDER, f"{uuid.uuid4()}_{filename}")
        logo_file.save(logo_path)

    # Save safety sheet
    safety_path = None
    if "safety_sheet" in files and files["safety_sheet"].filename:
        sheet_file = files["safety_sheet"]
        filename = secure_filename(sheet_file.filename)
        safety_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
        sheet_file.save(safety_path)

    # Weather icon path (optional)
    weather_icon_path = os.path.join(WEATHER_ICON_FOLDER, "weather_icon.png")
    if not os.path.exists(weather_icon_path):
        weather_icon_path = None

    # Scope AI Analysis
    ai_analysis = {}
    if data.get("enable_ai") == "on":
        project_id = data.get("project_name", "default_project").replace(" ", "_")
        scope_items = load_scope_for_project(project_id)
        ai_analysis = analyze_scope_vs_log(
            scope_items,
            data.get("work_done", ""),
            data.get("crew_notes", ""),
            data.get("safety_notes", "")
        )

    filename = f"daily_log_{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(GENERATED_FOLDER, filename)

    create_daily_log_pdf(
        data,
        image_paths,
        logo_path,
        ai_analysis,
        ai_analysis,
        pdf_path,
        weather_icon_path,
        safety_sheet_path=safety_path
    )

    return {"pdf_url": f"/generated/{filename}"}

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
