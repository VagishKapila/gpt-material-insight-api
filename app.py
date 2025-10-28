import os
import traceback
import json
import uuid
import requests
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log, parse_scope_file
from utils.weather_icon import download_weather_icon
from utils.image_tools import fix_image_orientation

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["GENERATED_FOLDER"] = "static/generated"
app.config["SCOPE_FOLDER"] = "static/scope"
app.config["LOGO_FOLDER"] = "static/logos"
app.config["ALLOWED_SCOPE_EXTENSIONS"] = {"pdf", "docx", "txt", "xlsx", "xls"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["GENERATED_FOLDER"], exist_ok=True)
os.makedirs(app.config["SCOPE_FOLDER"], exist_ok=True)
os.makedirs(app.config["LOGO_FOLDER"], exist_ok=True)

def allowed_scope_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config["ALLOWED_SCOPE_EXTENSIONS"]

@app.route("/")
def health():
    return "✅ Daily Log AI is up and running!"

@app.route("/form", methods=["GET"])
def form():
    return render_template("form.html")

@app.route("/get_weather", methods=["GET"])
def get_weather():
    location = request.args.get("location", "")
    if not location:
        return {"weather": "Unknown"}
    try:
        r = requests.get(f"https://wttr.in/{location}?format=%C+%t")
        return {"weather": r.text.strip()}
    except:
        return {"weather": "Unavailable"}

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        data = {
            "project_name": request.form.get("project_name", ""),
            "client_name": request.form.get("client_name", ""),
            "location": request.form.get("location", ""),
            "date": request.form.get("date", ""),
            "weather": request.form.get("weather", ""),
            "crew_notes": request.form.get("crew_notes", ""),
            "work_done": request.form.get("work_done", ""),
            "safety_notes": request.form.get("safety_notes", "")
        }

        session_id = str(uuid.uuid4())[:8]
        session_folder = os.path.join(app.config["UPLOAD_FOLDER"], session_id)
        os.makedirs(session_folder, exist_ok=True)

        images = []
        if "images" in request.files:
            for file in request.files.getlist("images"):
                if file.filename:
                    filename = secure_filename(file.filename)
                    path = os.path.join(session_folder, filename)
                    file.save(path)
                    fix_image_orientation(path)
                    images.append(path)

        safety_sheet_path = None
        if "safety_sheet" in request.files:
            file = request.files["safety_sheet"]
            if file.filename:
                filename = secure_filename(file.filename)
                safety_sheet_path = os.path.join(session_folder, filename)
                file.save(safety_sheet_path)

        logo_path = None
        if "logo" in request.files:
            file = request.files["logo"]
            if file.filename:
                filename = secure_filename(file.filename)
                logo_path = os.path.join(app.config["LOGO_FOLDER"], filename)
                file.save(logo_path)

        scope_path = None
        if "scope_doc" in request.files:
            file = request.files["scope_doc"]
            if file and allowed_scope_file(file.filename):
                filename = secure_filename(file.filename)
                scope_path = os.path.join(app.config["SCOPE_FOLDER"], filename)
                file.save(scope_path)

        ai_enabled = request.form.get("enable_ai", "on") == "on"
        ai_result = None
        if ai_enabled and scope_path:
            scope_text = parse_scope_file(scope_path)
            ai_result = analyze_scope_vs_log(scope_text, data)

        # Clean up NumPy or bool_ objects for JSON
        def safe_for_json(obj):
            if isinstance(obj, (int, float, str, bool)) or obj is None:
                return obj
            if hasattr(obj, "item"):  # NumPy types
                return obj.item()
            return str(obj)

        weather_icon_path = None
        if data["weather"]:
            weather_icon_path = download_weather_icon(data["weather"])

        preview_data = {
            "data": data,
            "images": images,
            "logo": logo_path,
            "ai_analysis": ai_result,
            "weather_icon": weather_icon_path,
            "safety_sheet_path": safety_sheet_path
        }

        # Sanitize before saving to JSON
        clean_preview = json.loads(json.dumps(preview_data, default=safe_for_json))

        preview_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{session_id}.json")
        with open(preview_path, "w") as f:
            json.dump(clean_preview, f)

        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

@app.route("/preview/<session_id>")
def preview(session_id):
    try:
        preview_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{session_id}.json")
        with open(preview_path, "r") as f:
            preview_data = json.load(f)

        return render_template(
            "preview.html",
            session_id=session_id,
            data=preview_data["data"],
            images=preview_data["images"],
            logo=preview_data["logo"],
            ai_analysis=preview_data["ai_analysis"],
        )
    except Exception as e:
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

@app.route("/finalize_preview", methods=["POST"])
def finalize_preview():
    try:
        session_id = request.form["session_id"]
        preview_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{session_id}.json")

        with open(preview_path, "r") as f:
            preview_data = json.load(f)

        # Update confidence values if user edited them
        ai = preview_data.get("ai_analysis", {})
        if "scored_items" in ai:
            for s in ai["scored_items"]:
                key = f"score_{s['scope'][:75]}"
                if key in request.form:
                    try:
                        s["confidence"] = int(request.form[key])
                        s["match"] = s["confidence"] >= 65
                    except:
                        pass

        pdf_filename = f"daily_log_{session_id}.pdf"
        save_path = os.path.join(app.config["GENERATED_FOLDER"], pdf_filename)

        create_daily_log_pdf(
            preview_data["data"],
            preview_data["images"],
            preview_data.get("logo"),
            ai,
            ai.get("completion", 0),
            save_path,
            preview_data.get("weather_icon"),
            preview_data.get("safety_sheet_path"),
        )

        return redirect(f"/generated/{pdf_filename}")

    except Exception as e:
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

@app.route("/generated/<filename>")
def serve_generated(filename):
    return send_from_directory(app.config["GENERATED_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)
