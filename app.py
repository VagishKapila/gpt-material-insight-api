from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
import datetime
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'
app.config['AUTOFILL_FOLDER'] = 'static/autofill'

# Ensure necessary folders exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['GENERATED_FOLDER'], app.config['AUTOFILL_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def health_check():
    return "✅ Server is running!"

@app.route("/form", methods=["GET"])
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        data = request.form.to_dict()
        print("📝 Received form data:", data)

        # Save uploaded images
        image_paths = []
        images = request.files.getlist("images")
        for img in images:
            if img and img.filename != "":
                filename = secure_filename(img.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img.save(path)
                image_paths.append(path)

        # Optional: Logo upload
        logo_path = None
        logo = request.files.get("logo")
        if logo and logo.filename != "":
            logo_filename = secure_filename(logo.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
            logo.save(logo_path)

        # Optional: Weather icon upload
        weather_icon_path = None
        weather_icon = request.files.get("weather_icon")
        if weather_icon and weather_icon.filename != "":
            icon_filename = secure_filename(weather_icon.filename)
            weather_icon_path = os.path.join(app.config['UPLOAD_FOLDER'], icon_filename)
            weather_icon.save(weather_icon_path)

        # Optional: Safety sheet upload
        safety_path = None
        safety = request.files.get("safety_sheet")
        if safety and safety.filename != "":
            safety_filename = secure_filename(safety.filename)
            safety_path = os.path.join(app.config['UPLOAD_FOLDER'], safety_filename)
            safety.save(safety_path)

        # Scope text & AI Analysis
        progress_report = data.get("progress_report", "")
        ai_analysis = data.get("ai_analysis", "")

        # Save path
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        pdf_filename = f"log_{timestamp}.pdf"
        save_path = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)

        print("📄 Generating PDF...")
        create_daily_log_pdf(
            data,
            image_paths,
            logo_path=logo_path,
            ai_analysis=ai_analysis,
            progress_report=progress_report,  # ✅ FIXED KEY
            save_path=save_path,
            weather_icon_path=weather_icon_path,
            safety_sheet_path=safety_path
        )
        print("✅ PDF generated:", save_path)

        return {"pdf_url": f"/generated/{pdf_filename}"}

    except Exception as e:
        print("❌ Error during PDF generation:", str(e))
        return {"error": str(e)}, 500

@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)
