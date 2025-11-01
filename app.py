# app.py — v2025.11.01 (Stable + Video Thumbnail Integration)
import os
import json
import uuid
import traceback
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

# --- Local imports ---
from utils.compare_scope_vs_log import analyze_scope_vs_log
from utils.pdf_generator import create_daily_log_pdf
from utils.video_tools import generate_video_thumbnail  # ✅ Added for video thumbnails

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

# ---------------------------------------------------------------------
# 🩺 Health Check
# ---------------------------------------------------------------------
@app.route("/")
def health():
    return "✅ Nails & Notes AI Log is running!"

# ---------------------------------------------------------------------
# 🧱 Form Route
# ---------------------------------------------------------------------
@app.route("/form")
def form():
    return render_template("form.html", datetime=datetime)

# ---------------------------------------------------------------------
# 🚀 Generate Form / Handle Uploads
# ---------------------------------------------------------------------
@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        print("\n📥 Incoming request.files keys:", list(request.files.keys()))
        print("📥 request.form keys:", list(request.form.keys()))

        # --- Core Form Data ---
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

        # -----------------------------------------------------------------
        # 💾 Utility to save any uploaded file
        # -----------------------------------------------------------------
        def save_file(field, folder):
            if field in request.files and request.files[field].filename:
                file = request.files[field]
                filename = secure_filename(file.filename)
                path = os.path.join(folder, f"{session_id}_{filename}")
                file.save(path)
                print(f"✅ Saved {field} to {path}")
                return path
            return None

        # -----------------------------------------------------------------
        # 📄 Save optional uploads (logo, safety, scope)
        # -----------------------------------------------------------------
        logo_path = save_file("logo", LOGO_FOLDER)
        safety_path = save_file("safety_sheet", SAFETY_FOLDER)
        scope_path = save_file("scope_doc", SCOPE_FOLDER)

        # -----------------------------------------------------------------
        # 📸 Handle jobsite media (images + videos)
        # -----------------------------------------------------------------
        media_file_keys = [k for k in request.files if k == "media_files" or k.startswith("media_files[")]
        allowed_image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
        allowed_video_exts = {".mp4", ".mov", ".avi", ".mkv"}

        for key in media_file_keys:
            for file in request.files.getlist(key):
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1].lower()
                    safe_filename = f"{session_id}_{uuid.uuid4().hex}{ext}"
                    save_path = os.path.join(UPLOAD_FOLDER, safe_filename)
                    file.save(save_path)
                    print(f"📦 Uploaded jobsite media: {save_path}")

                    # ✅ Images
                    if ext in allowed_image_exts:
                        image_paths.append(save_path)
                        print(f"🖼️ Added image file: {file.filename}")

                    # ✅ Videos (generate thumbnail)
                    elif ext in allowed_video_exts:
                        print(f"🎥 Processing video: {file.filename}")
                        thumb = generate_video_thumbnail(save_path)
                        if thumb and os.path.exists(thumb):
                            image_paths.append(thumb)
                            print(f"✅ Added video thumbnail: {thumb}")
                        else:
                            print(f"⚠️ Thumbnail generation failed for {file.filename}, skipping preview.")

                    else:
                        print(f"⚠️ Skipped unsupported file type: {file.filename}")

        # -----------------------------------------------------------------
        # 🤖 AI Scope Comparison
        # -----------------------------------------------------------------
        ai_results = {}
        progress_report = {}

        if request.form.get("enable_ai") and scope_path:
            try:
                ai_results = analyze_scope_vs_log(scope_path, form_data, image_paths)
                print("✅ AI analysis completed successfully.")
            except Exception as e:
                traceback.print_exc()
                ai_results = {"error": f"AI analysis failed: {str(e)}"}

        # -----------------------------------------------------------------
        # 💾 Save session data
        # -----------------------------------------------------------------
        session_data = {
            "form_data": form_data,
            "image_paths": image_paths,
            "logo_path": logo_path,
            "ai_results": ai_results,
            "progress_report": progress_report,
            "weather_icon_path": None,
            "safety_sheet_path": safety_path,
        }

        with open(os.path.join(SESSION_FOLDER, f"{session_id}.json"), "w") as f:
            json.dump(session_data, f, indent=2)

        print(f"💾 Saved session {session_id} with {len(image_paths)} image/video previews.")
        return redirect(url_for("preview", session_id=session_id))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Error generating form: {str(e)}", 500

# ---------------------------------------------------------------------
# 🧠 Preview Page
# ---------------------------------------------------------------------
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
        return f"❌ Failed to load preview: {str(e)}", 500

# ---------------------------------------------------------------------
# 🧾 Submit Preview → Generate PDF
# ---------------------------------------------------------------------
@app.route("/submit_preview", methods=["POST"])
def submit_preview():
    session_id = request.form.get("session_id")
    if not session_id:
        return "Missing session ID", 400

    json_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    if not os.path.exists(json_path):
        return f"❌ Session not found: {session_id}", 404

    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        total_items = int(request.form.get("total_items", 0))
        scored_items = []

        for i in range(total_items):
            scope = request.form.get(f"scope_{i}", "")
            confidence = int(request.form.get(f"confidence_{i}", 0))
            match = f"match_{i}" in request.form
            matched_image = request.form.get(f"matched_image_{i}", "").strip() or None

            scored_items.append({
                "scope": scope,
                "confidence": confidence,
                "match": match,
                "matched_image": matched_image
            })

        estimated_completion = sum(i["confidence"] for i in scored_items if i["match"]) / max(len(scored_items), 1)

        data["ai_results"] = {
            "completion": round(estimated_completion, 1),
            "scored_items": scored_items,
            "out_of_scope": data.get("ai_results", {}).get("out_of_scope", [])
        }

        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

        pdf_name = f"{session_id}_daily_log.pdf"
        save_path = os.path.join(GENERATED_FOLDER, pdf_name)

        print(f"🧱 Generating PDF for session {session_id}...")
        create_daily_log_pdf(
            data=data.get("form_data", {}),
            image_paths=data.get("image_paths", []),
            logo_path=data.get("logo_path"),
            ai_analysis=data.get("ai_results"),
            progress_report=data.get("progress_report"),
            save_path=save_path,
            weather_icon_path=data.get("weather_icon_path"),
            safety_sheet_path=data.get("safety_sheet_path"),
        )
        print(f"✅ PDF generated successfully: {pdf_name}")
        return redirect(url_for("serve_pdf", filename=pdf_name))

    except Exception as e:
        traceback.print_exc()
        return f"❌ Failed to generate PDF: {str(e)}", 500

# ---------------------------------------------------------------------
# 📂 Serve Generated PDFs
# ---------------------------------------------------------------------
@app.route("/generated/<filename>")
def serve_pdf(filename):
    path = os.path.join(GENERATED_FOLDER, filename)
    if not os.path.exists(path):
        return f"❌ File not found: {filename}", 404
    return send_from_directory(GENERATED_FOLDER, filename)

# ---------------------------------------------------------------------
# 🧩 Debug Sessions
# ---------------------------------------------------------------------
@app.route("/debug_sessions")
def debug_sessions():
    try:
        session_files = os.listdir(SESSION_FOLDER)
        session_links = []
        for file in session_files:
            if file.endswith(".json"):
                session_id = file.replace(".json", "")
                session_links.append(f'<li><a href="/preview/{session_id}">{session_id}</a></li>')
        return f"<h2>🧠 Debug: Saved Sessions</h2><ul>{''.join(session_links)}</ul>"
    except Exception as e:
        return f"Failed to load sessions: {str(e)}", 500

# ---------------------------------------------------------------------
# 🚦 Run App (✅ Single Run Block)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # default to 5000 locally
    print(f"🚀 Starting server on port {port} ...")  # 👈 Add this line
    app.run(host="0.0.0.0", port=port, debug=True)
