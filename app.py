import os
import json
import uuid
import traceback
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

from utils.compare_scope_vs_log import analyze_scope_vs_log
from utils.pdf_generator import create_daily_log_pdf
from utils.video_tools import generate_video_thumbnail

app = Flask(__name__)

# ---------------------------------------------------------------------
# 📁 Folder Setup
# ---------------------------------------------------------------------
UPLOAD_FOLDER = "static/uploads"
GENERATED_FOLDER = "static/generated"
SCOPE_FOLDER = "static/scope"
SAFETY_FOLDER = "static/safety"
LOGO_FOLDER = "static/logo"
SESSION_FOLDER = "session_data"

for folder in [UPLOAD_FOLDER, GENERATED_FOLDER, SCOPE_FOLDER, SAFETY_FOLDER, LOGO_FOLDER, SESSION_FOLDER]:
    os.makedirs(folder, exist_ok=True)


@app.route("/")
def health():
    return "✅ Nails & Notes AI Log is running!"


@app.route("/form")
def form():
    return render_template("form.html", datetime=datetime)


@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        print("\n📥 Incoming request.files keys:", list(request.files.keys()))
        print("📥 request.form keys:", list(request.form.keys()))

        # Core form data
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
        media_items, scope_path, safety_path, logo_path = [], None, None, None

        def save_file(field, folder):
            if field in request.files and request.files[field].filename:
                file = request.files[field]
                filename = secure_filename(file.filename)
                path = os.path.join(folder, f"{session_id}_{filename}")
                file.save(path)
                print(f"✅ Saved {field} to {path}")
                return path
            return None

        logo_path = save_file("logo", LOGO_FOLDER)
        safety_path = save_file("safety_sheet", SAFETY_FOLDER)
        scope_path = save_file("scope_doc", SCOPE_FOLDER)

        allowed_images = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
        allowed_videos = {".mp4", ".mov", ".avi", ".mkv"}

        for key in request.files:
            if key.startswith("media_files"):
                for file in request.files.getlist(key):
                    if not file or not file.filename:
                        continue
                    ext = os.path.splitext(file.filename)[1].lower()
                    safe_name = f"{session_id}_{uuid.uuid4().hex}{ext}"
                    save_path = os.path.join(UPLOAD_FOLDER, safe_name)
                    file.save(save_path)
                    print(f"📦 Saved media: {save_path}")

                    if ext in allowed_images:
                        media_items.append({"type": "image", "path": save_path})
                    elif ext in allowed_videos:
                        print(f"🎥 Generating thumbnail for: {file.filename}")
                        thumb = generate_video_thumbnail(save_path)
                        if thumb and os.path.exists(thumb):
                            media_items.append({
                                "type": "video",
                                "path": save_path,
                                "thumbnail": thumb
                            })
                            print(f"✅ Video thumbnail added: {thumb}")
                        else:
                            print(f"⚠️ Failed to create thumbnail for: {file.filename}")
                    else:
                        print(f"⚠️ Unsupported file type: {file.filename}")

        ai_results, progress_report = {}, {}
        if request.form.get("enable_ai") and scope_path:
            try:
                ai_results = analyze_scope_vs_log(scope_path, form_data, [m["path"] for m in media_items])
                print("✅ AI analysis completed.")
            except Exception as e:
                traceback.print_exc()
                ai_results = {"error": f"AI failed: {e}"}

        session_data = {
            "form_data": form_data,
            "media_items": media_items,
            "logo_path": logo_path,
            "ai_results": ai_results,
            "progress_report": progress_report,
            "weather_icon_path": None,
            "safety_sheet_path": safety_path,
        }

        with open(os.path.join(SESSION_FOLDER, f"{session_id}.json"), "w") as f:
            json.dump(session_data, f, indent=2)

        print(f"💾 Session saved {session_id} with {len(media_items)} media entries.")
        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error generating form: {str(e)}", 500


@app.route("/preview/<session_id>")
def preview(session_id):
    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if not os.path.exists(json_path):
        return f"❌ Session not found: {session_id}", 404

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        print(f"🧩 Loaded session {session_id} for preview.")
        return render_template("preview.html", session_id=session_id, **data)
    except Exception as e:
        traceback.print_exc()
        return f"❌ Failed to load preview: {e}", 500


@app.route("/submit_preview", methods=["POST"])
def submit_preview():
    session_id = request.form.get("session_id")
    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")

    if not os.path.exists(json_path):
        return "❌ Session not found", 404

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        pdf_name = f"{session_id}_daily_log.pdf"
        save_path = os.path.join(GENERATED_FOLDER, pdf_name)
        create_daily_log_pdf(
            data=data.get("form_data", {}),
            image_paths=[m["path"] for m in data.get("media_items", [])],
            logo_path=data.get("logo_path"),
            ai_analysis=data.get("ai_results"),
            progress_report=data.get("progress_report"),
            save_path=save_path,
            weather_icon_path=data.get("weather_icon_path"),
            safety_sheet_path=data.get("safety_sheet_path"),
        )
        print(f"✅ PDF generated successfully.")
        return redirect(url_for("serve_pdf", filename=pdf_name))
    except Exception as e:
        traceback.print_exc()
        return f"❌ Failed to generate PDF: {e}", 500


@app.route("/generated/<filename>")
def serve_pdf(filename):
    return send_from_directory(GENERATED_FOLDER, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
