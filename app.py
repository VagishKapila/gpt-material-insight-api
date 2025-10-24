from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import json
import requests
import uuid
from image_utils import preprocess_images  # Make sure this is saved
from pdf_generator import create_daily_log_pdf

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
AUTOFILL_FOLDER = "static/autofill"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(AUTOFILL_FOLDER, exist_ok=True)

@app.route("/")
def health_check():
    return "Nails & Notes AI is live!"

@app.route("/form", methods=["GET"])
def daily_log_form():
    return render_template("form.html")

@app.route("/get_weather", methods=["GET"])
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return jsonify({"weather": ""})
    try:
        res = requests.get(f"https://wttr.in/{location}?format=%C+%t")
        weather = res.text.strip()
        if "Unknown location" in weather or not weather:
            raise Exception("Invalid location")
        return jsonify({"weather": weather})
    except:
        return jsonify({"weather": "Weather unavailable"})

@app.route("/generate_form", methods=["POST"])
def generate_pdf():
    form = request.form
    images = request.files.getlist("images")
    logo = request.files.get("logo")
    safety_sheet = request.files.get("safety_sheet")
    enable_ai = form.get("enable_ai") == "on"
    location = form.get("location", "Unknown")
    project_name = form.get("project_name", "Unnamed Project")

    uid = str(uuid.uuid4())
    weather_icon_path = None
    logo_path = None
    safety_sheet_path = None

    # Save and preprocess images
    image_paths = []
    for img_file in images:
        img_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{img_file.filename}")
        img_file.save(img_path)
        image_paths.append(img_path)

    processed_images = preprocess_images(image_paths)

    # Logo
    if logo and logo.filename:
        logo_path_raw = os.path.join(UPLOAD_FOLDER, f"{uid}_logo_{logo.filename}")
        logo.save(logo_path_raw)
        processed = preprocess_images([logo_path_raw])
        logo_path = processed[0] if processed else None

    # Safety sheet
    if safety_sheet and safety_sheet.filename:
        safety_path_raw = os.path.join(UPLOAD_FOLDER, f"{uid}_safety_{safety_sheet.filename}")
        safety_sheet.save(safety_path_raw)
        processed = preprocess_images([safety_path_raw])
        safety_sheet_path = processed[0] if processed else None

    # Weather icon logic (optional - use real icon mapping)
    if "sun" in form.get("weather", "").lower():
        weather_icon_path = "static/weather/sunny.png"
    elif "rain" in form.get("weather", "").lower():
        weather_icon_path = "static/weather/rain.png"
    elif "cloud" in form.get("weather", "").lower():
        weather_icon_path = "static/weather/cloudy.png"

    # Autofill save
    autofill_data = {
        k: v for k, v in form.items() if k not in ["weather", "images", "logo", "safety_sheet"]
    }
    autofill_file = os.path.join(AUTOFILL_FOLDER, f"{project_name}.json")
    with open(autofill_file, "w") as f:
        json.dump(autofill_data, f)

    # Final PDF path
    final_pdf = os.path.join(GENERATED_FOLDER, f"{uid}_daily_log.pdf")

    # AI & Progress Placeholder
    ai_analysis = "AI-powered visual analysis included." if enable_ai else ""
    progress_report = "Project progress aligned with scope of work." if enable_ai else ""

    create_daily_log_pdf(
        data=form,
        image_paths=processed_images,
        logo_path=logo_path,
        ai_analysis=ai_analysis,
        progress_report=progress_report,
        save_path=final_pdf,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_sheet_path,
    )

    return jsonify({"pdf_url": f"/generated/{os.path.basename(final_pdf)}"})

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)
