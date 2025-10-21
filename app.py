from utils.image_analyzer import analyze_and_overlay
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import datetime
from utils.pdf_generator import create_daily_log_pdf
import requests

# --- Flask setup ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload


# --- Health check ---
@app.route("/")
def home():
    return "Nails & Notes API is live!"


# --- Optional Web Form ---
@app.route("/form", methods=["GET"])
def show_form():
    return render_template("form.html")


# --- Weather fetch helper ---
@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return jsonify({"error": "No location provided"}), 400
    try:
        response = requests.get(f"https://wttr.in/{location}?format=1", timeout=3)
        weather = response.text.strip()
        return jsonify({"weather": weather})
    except Exception as e:
        print(f"[Weather API Error] {e}")
        return jsonify({"error": "Unable to fetch weather"}), 500


# --- API Endpoint for GPT Action ---
@app.route("/generate", methods=["POST"])
def generate_log():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload"}), 400

        # Extract JSON fields
        project_name = data.get("project_name", "Untitled Project")
        address = data.get("address", "")
        general_contractor = data.get("general_contractor", "")
        client_name = data.get("client_name", "")
        date = data.get("date", datetime.date.today().isoformat())
        crew_notes = data.get("crew_notes", "")
        work_done = data.get("work_done", "")
        safety_notes = data.get("safety_notes", "")
        weather = data.get("weather", "")
        photo_urls = data.get("photo_urls", [])
        logo_url = data.get("logo_url")

        # --- Save downloaded photos temporarily ---
        saved_photos = []
        for i, url in enumerate(photo_urls):
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"photo_{i}.jpg")
                    with open(file_path, "wb") as f:
                        f.write(r.content)
                    saved_photos.append(file_path)
            except Exception as e:
                print(f"Error downloading image: {e}")

        # --- Save logo if provided ---
        logo_path = None
        if logo_url:
            try:
                r = requests.get(logo_url, timeout=5)
                if r.status_code == 200:
                    logo_path = os.path.join(app.config["UPLOAD_FOLDER"], "logo.jpg")
                    with open(logo_path, "wb") as f:
                        f.write(r.content)
            except Exception as e:
                print(f"Error downloading logo: {e}")

        # --- Generate PDF ---
        output_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(output_dir, f"{project_name.replace(' ', '_')}_Report_{date}.pdf")

        create_daily_log_pdf(
            {
                "project_name": project_name,
                "project_address": address,
                "weather": weather,
                "date": date,
                "crew_notes": crew_notes,
                "work_done": work_done,
                "safety_notes": safety_notes,
                "equipment_used": data.get("equipment_used", ""),
                "material_summary": data.get("material_summary", ""),
                "hours_worked": data.get("hours_worked", ""),
            },
            pdf_path,
            photo_paths=saved_photos,
            logo_path=logo_path,
            include_page_2=True
        )

        # --- Save file to static folder and return URL ---
        file_name = os.path.basename(pdf_path)
        static_folder = os.path.join("static", "generated")
        os.makedirs(static_folder, exist_ok=True)

        final_path = os.path.join(static_folder, file_name)
        os.replace(pdf_path, final_path)

        public_url = f"https://nails-and-notes.onrender.com/generated/{file_name}"
        return jsonify({"pdf_url": public_url})

    except Exception as e:
        print(f"[Server Error] {e}")
        return jsonify({"error": f"Server error: {e}"}), 500


# --- Serve generated PDFs publicly ---
@app.route("/generated/<filename>")
def serve_pdf(filename):
    file_path = os.path.join("static/generated", filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=False)
    else:
        return "File not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
