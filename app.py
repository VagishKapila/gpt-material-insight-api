from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime
import os
import requests

# Flask app setup
app = Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")

# Port config (for Render or local)
port = int(os.environ.get("PORT", 10000))

# ─────────────────────────────────────────
# ✅ HEALTH CHECK ROUTE
@app.route("/")
def index():
    return "✅ Daily Log AI is running"

# ─────────────────────────────────────────
# ✅ WEATHER LOOKUP ROUTE
@app.route("/get_weather")
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return jsonify({"error": "Location not provided"}), 400
    try:
        res = requests.get(f"https://wttr.in/{location}?format=3", timeout=5)
        if res.status_code == 200:
            return jsonify({"weather": res.text})
        else:
            return jsonify({"error": "Weather service not available"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────
# ✅ FORM VIEW (HTML Page)
@app.route("/form")
def form():
    return render_template("form.html")  # Make sure templates/form.html exists

# ─────────────────────────────────────────
# ✅ FORM SUBMISSION HANDLER
@app.route("/generate_form", methods=["POST"])
def generate_form():
    data = request.form.to_dict()
    # Log received data (for debugging)
    print("📄 Received form submission:", data)

    # TODO: Add logic here to generate the daily log PDF using uploaded data and photos
    # You can call your existing function here, for example:
    # pdf_url = create_daily_log_pdf(data)
    
    return jsonify({
        "message": "Form received successfully.",
        "data": data,
        "note": "PDF generation logic not yet included in this route"
    })

# ─────────────────────────────────────────
# ✅ MAIN LAUNCHER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
