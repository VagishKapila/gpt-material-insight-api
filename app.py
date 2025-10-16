from flask import Flask, request, render_template, send_file, redirect
from werkzeug.utils import secure_filename
import os
import tempfile
from utils.pdf_generator import create_daily_log_pdf

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
        # Extract form data
        form = request.form
        files = request.files.getlist("photos")

        # Save uploaded files
        saved_files = []
        for f in files:
            if f and f.filename:
                filename = secure_filename(f.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(filepath)
                saved_files.append(filepath)

        # Prepare data dictionary
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
            "photos": saved_files
        }

        # Generate PDF
        output_dir = tempfile.mkdtemp()
        pdf_path = create_daily_log_pdf(data, output_dir)

        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        print(f"[Server Error] {e}")
        return "Log submitted successfully!"

if __name__ == "__main__":
    app.run(debug=True)
