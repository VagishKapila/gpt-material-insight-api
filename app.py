import os, json, uuid, traceback
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

from utils.compare_scope_vs_log import analyze_scope_vs_log
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)

# --- Folders ---
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
SAFETY_FOLDER = "static/safety"
LOGO_FOLDER = "static/logo"
SESSION_FOLDER = "session_data"

for f in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER, SAFETY_FOLDER, LOGO_FOLDER, SESSION_FOLDER]:
    os.makedirs(f, exist_ok=True)

# --- Health Check ---
@app.route("/")
def health():
    return "✅ Nails & Notes AI Log is running!"

# --- Form Route ---
@app.route("/form")
def form():
    return render_template("form.html", datetime=datetime)

# --- Handle Form Submission ---
@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        form_data = {
            "project_name": request.form.get("project_name"),
            "client_name": request.form.get("client_name"),
            "location": request.form.get("location"),
            "date": request.form.get("date"),
            "weather": request.form.get("weather"),
            "work_done": request.form.get("work_done"),
            "crew_notes": request.form.get("crew_notes"),
            "safety_notes": request.form.get("safety_notes"),
        }

        session_id = str(uuid.uuid4())
        image_paths, scope_path, safety_path, logo_path = [], None, None, None

        def save_file(field, folder):
            if field in request.files and request.files[field].filename:
                f = request.files[field]
                filename = secure_filename(f.filename)
                path = os.path.join(folder, f"{session_id}_{filename}")
                f.save(path)
                return path
            return None

        logo_path = save_file("logo", LOGO_FOLDER)
        safety_path = save_file("safety_sheet", SAFETY_FOLDER)
        scope_path = save_file("scope_doc", SCOPE_FOLDER)

        if "images" in request.files:
            for img in request.files.getlist("images"):
                if img.filename:
                    filename = secure_filename(img.filename)
                    path = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
                    img.save(path)
                    image_paths.append(path)

        session_data = {
            "form_data": form_data,
            "image_paths": image_paths,
            "logo_path": logo_path,
            "progress_report": {},
            "ai_results": {},
            "weather_icon_path": None,
            "safety_sheet_path": safety_path,
            "scope_path": scope_path,
        }

        with open(os.path.join(SESSION_FOLDER, f"{session_id}.json"), "w") as f:
            json.dump(session_data, f, indent=2)

        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error generating form: {str(e)}", 500

# --- Preview Page ---
@app.route("/preview/<session_id>")
def preview(session_id):
    try:
        path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        if not os.path.exists(path):
            return f"❌ Session not found: {session_id}", 404

        with open(path) as f:
            data = json.load(f)

        pdf_filename = f"{session_id}_daily_log.pdf"
        pdf_path = os.path.join(GENERATED_FOLDER, pdf_filename)
        pdf_exists = os.path.exists(pdf_path)

        return render_template(
            "preview.html",
            session_id=session_id,
            pdf_filename=pdf_filename,
            pdf_exists=pdf_exists,
            **data
        )
    except Exception as e:
        traceback.print_exc()
        return f"❌ Failed to load preview: {str(e)}", 500

# --- AI Scope Analysis ---
@app.route("/analyze_scope/<session_id>", methods=["POST"])
def analyze_scope(session_id):
    try:
        path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        if not os.path.exists(path):
            return jsonify({"error": "Session not found"}), 404

        with open(path) as f:
            data = json.load(f)

        if not data.get("scope_path"):
            return jsonify({"error": "Scope file not uploaded"}), 400

        ai_results = analyze_scope_vs_log(
            data["scope_path"], data["form_data"], data.get("image_paths", [])
        )
        data["ai_results"] = ai_results

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Add Image ---
@app.route("/add_image/<session_id>", methods=["POST"])
def add_image(session_id):
    try:
        path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        with open(path) as f:
            data = json.load(f)
        for img in request.files.getlist("new_images"):
            if img.filename:
                filename = secure_filename(img.filename)
                p = os.path.join(UPLOAD_FOLDER, f"{session_id}_{filename}")
                img.save(p)
                data["image_paths"].append(p)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Remove Image ---
@app.route("/remove_image/<session_id>", methods=["POST"])
def remove_image(session_id):
    try:
        path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        with open(path) as f:
            data = json.load(f)
        img_to_remove = request.json.get("image_path")
        if img_to_remove in data["image_paths"]:
            data["image_paths"].remove(img_to_remove)
            if os.path.exists(img_to_remove):
                os.remove(img_to_remove)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Final Submission + Generate PDF ---
@app.route("/submit_preview", methods=["POST"])
def submit_preview():
    try:
        session_id = request.form.get("session_id")
        path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
        with open(path) as f:
            data = json.load(f)

        total_items = int(request.form.get("total_items", 0))
        scored = []
        for i in range(total_items):
            scored.append({
                "scope": request.form.get(f"scope_{i}"),
                "confidence": int(request.form.get(f"confidence_{i}", 0)),
                "match": f"match_{i}" in request.form,
                "matched_image": request.form.get(f"matched_image_{i}") or None
            })

        completion = round(
            sum(i["confidence"] for i in scored if i["match"]) / max(len(scored), 1), 1
        )

        data["ai_results"] = {
            "completion": completion,
            "scored_items": scored,
            "out_of_scope": data.get("ai_results", {}).get("out_of_scope", [])
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        pdf_name = f"{session_id}_daily_log.pdf"
        pdf_path = os.path.join(GENERATED_FOLDER, pdf_name)

        create_daily_log_pdf(
            data=data.get("form_data", {}),
            image_paths=data.get("image_paths", []),
            logo_path=data.get("logo_path"),
            ai_analysis=data.get("ai_results"),
            progress_report=data.get("progress_report"),
            save_path=pdf_path,
            weather_icon_path=data.get("weather_icon_path"),
            safety_sheet_path=data.get("safety_sheet_path"),
        )

        return redirect(url_for("serve_pdf", filename=pdf_name))
    except Exception as e:
        traceback.print_exc()
        return f"❌ Failed to generate PDF: {str(e)}", 500

# --- Serve PDFs ---
@app.route("/generated/<filename>")
def serve_pdf(filename):
    pdf_path = os.path.join(GENERATED_FOLDER, filename)
    if not os.path.exists(pdf_path):
        return f"❌ File not found: {filename}", 404
    return send_from_directory(GENERATED_FOLDER, filename, mimetype="application/pdf")

# --- Debug Route ---
@app.route("/debug_sessions")
def debug_sessions():
    try:
        sessions = [
            f.split(".json")[0]
            for f in os.listdir(SESSION_FOLDER)
            if f.endswith(".json")
        ]
        links = [f'<li><a href="/preview/{sid}">{sid}</a></li>' for sid in sessions]
        return f"<h2>🧠 Debug Sessions</h2><ul>{''.join(links)}</ul>"
    except Exception as e:
        return f"Failed to load sessions: {str(e)}", 500

# --- Start Server ---
if __name__ == "__main__":
    app.run(debug=True)
