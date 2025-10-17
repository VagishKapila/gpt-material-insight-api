from flask import Flask, request, render_template, send_file, redirect
from werkzeug.utils import secure_filename
import os
import tempfile
from utils.pdf_generator import create_daily_log_pdf

# ✅ must be defined BEFORE using @app.route
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

@app.route("/")
def home():
    return "Server is running!"

@app.route("/form", methods=["GET"])
def show_form():
    return render_template("form.html")

@app.route("/submit", methods=["GET", "POST"])
def submit_log():
    if request.method == "GET":
        return redirect("/form")  # Prevent Method Not Allowed on refresh

    try:
        form = request.form
        all_files = request.files

        # Handle photo uploads
        photos = request.files.getlist("photos")
        saved_photos = []
        for f in photos:
            if f and f.filename:
                filename = secure_filename(f.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(path)
                saved_photos.append(path)

        # Handle logo
        logo = all_files.get("logo")
        logo_path = None
        if logo and logo.filename:
            logo_filename = secure_filename(logo.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
            logo.save(logo_path)

        # Handle weather icon
        weather_icon = all_files.get("weather_icon")
        weather_icon_path = None
        if weather_icon and weather_icon.filename:
            weather_icon_filename = secure_filename(weather_icon.filename)
            weather_icon_path = os.path.join(app.config['UPLOAD_FOLDER'], weather_icon_filename)
            weather_icon.save(weather_icon_path)

        # Include Page 2 toggle
        include_page_2 = 'include_page_2' in form

        # Prepare all data for PDF
        data = {
            "date": form.get("date"),
            "project_name": form.get("project_name"),
            "client_name": form.get("client_name"),
            "job_number": form.get("job_number"),
            "prepared_by": form.get("prepared_by"),
            "location": form.get("location"),
            "gc_or_sub": form.get("gc_or_sub"),
            "crew_notes": form.get("crew_notes"),
            "work_done": form.get("work_done"),
            "deliveries": form.get("deliveries"),
            "inspections": form.get("inspections"),
            "equipment_used": form.get("equipment_used"),
            "safety_notes": form.get("safety_notes"),
            "weather": form.get("weather"),
            "notes": form.get("notes"),
            "photos": saved_photos,
            "logo_path": logo_path,
            "weather_icon_path": weather_icon_path,
            "include_page_2": include_page_2
        }

        # Generate PDF
        output_dir = tempfile.mkdtemp()
        pdf_path = create_daily_log_pdf(data, output_dir)

        return send_file(pdf_path, as_attachment=True, download_name="Daily_Log.pdf")

    except Exception as e:
        print(f"[Server Error] {e}")
        return f"Error occurred during log submission: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
