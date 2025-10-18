# app.py
from flask import Flask, render_template, request, send_file, jsonify
import os
from werkzeug.utils import secure_filename
import tempfile
import requests

app = Flask(__name__)

@app.route("/")
def index():
    return "Server is running. Use /form to access the Daily Log Form."

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    form_data = request.form.to_dict()

    logo_file = request.files.get("logo")
    photos = request.files.getlist("photos")

    include_page_2 = 'include_page_2' in request.form

    with tempfile.TemporaryDirectory() as temp_dir:
        logo_path = None
        if logo_file:
            logo_filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(temp_dir, logo_filename)
            logo_file.save(logo_path)

        photo_paths = []
        for photo in photos[:20]:
            if photo:
                photo_filename = secure_filename(photo.filename)
                path = os.path.join(temp_dir, photo_filename)
                photo.save(path)
                photo_paths.append(path)

        output_path = os.path.join(temp_dir, "Daily_Log.pdf")
        create_daily_log_pdf(form_data, output_path, photo_paths, logo_path, include_page_2)
        return send_file(output_path, as_attachment=True)

@app.route("/get_weather")
def get_weather():
    location = request.args.get("location")
    if not location:
        return jsonify({"error": "Missing location"}), 400

    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            current_condition = data["current_condition"][0]
            weather_desc = current_condition["weatherDesc"][0]["value"]
            temperature_c = current_condition["temp_C"]

            weather_icons = {
                "Clear": "☀️",
                "Sunny": "☀️",
                "Partly Cloudy": "🌤️",
                "Cloudy": "☁️",
                "Overcast": "☁️",
                "Rain": "🌧️",
                "Drizzle": "🌦️",
                "Thunderstorm": "⛈️",
                "Snow": "❄️",
                "Mist": "🌫️",
                "Fog": "🌫️",
                "Haze": "🌁",
            }

            # Fallback to ❓ if unknown
            icon = weather_icons.get(weather_desc, "❓")

            return jsonify({
                "weather": weather_desc,
                "icon": icon,
                "temperature": temperature_c
            })
        else:
            return jsonify({"error": "Weather service failed"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500
