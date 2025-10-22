from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime
import requests, os
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/")
def index():
    return "✅ Daily Log AI is running"

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return jsonify({"error": "No location provided"}), 400
    try:
        url = f"https://wttr.in/{location}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return jsonify({"weather": response.text.strip()})
        return jsonify({"error": "Weather unavailable"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = request.form.to_dict()
        photos = request.files.getlist("photos")
        logo = request.files.get("logo")

        upload_dir = "static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        photo_paths, logo_path = [], None

        for photo in photos[:20]:
            if photo and photo.filename:
                photo_path = os.path.join(upload_dir, photo.filename)
                photo.save(photo_path)
                photo_paths.append(photo_path)

        if logo and logo.filename:
            logo_path = os.path.join(upload_dir, logo.filename)
            logo.save(logo_path)

        include_page_2 = "include_page_2" in form_data

        # Generate PDF
        pdf_filename = create_daily_log_pdf(
            form_data,
            photo_paths=photo_paths,
            logo_path=logo_path,
            include_page_2=include_page_2
        )

        pdf_url = f"/generated/{pdf_filename}"
        return jsonify({"pdf_url": pdf_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generated/<path:filename>")
def serve_generated(filename):
    return send_from_directory("static/generated", filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
