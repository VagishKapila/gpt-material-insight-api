from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 🔧 Define upload folders
UPLOAD_FOLDER = 'static/uploads'
COMPRESSED_FOLDER = 'static/compressed'

# 🔧 Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)


@app.route("/upload_media_test", methods=["POST"])
def upload_media():
    """
    Handles file uploads (images + videos).
    Images: saved as-is.
    Videos: compressed if ffmpeg is available, else skipped.
    """
    uploaded_files = request.files.getlist("media_files")
    saved_files = []

    for f in uploaded_files:
        filename = secure_filename(f.filename)
        file_ext = filename.rsplit('.', 1)[-1].lower()
        temp_name = f"{uuid.uuid4().hex}.{file_ext}"
        save_path = os.path.join(UPLOAD_FOLDER, temp_name)
        f.save(save_path)

        # 🎥 If it's a video, compress with ffmpeg
        if file_ext in ["mp4", "mov", "avi", "mkv"]:
            compressed_name = f"compressed_{temp_name}"
            compressed_path = os.path.join(COMPRESSED_FOLDER, compressed_name)

            ffmpeg_cmd = [
                "ffmpeg", "-i", save_path,
                "-vcodec", "libx264", "-crf", "28",
                "-preset", "veryfast", "-y", compressed_path
            ]

            try:
                subprocess.run(ffmpeg_cmd, check=True)
                os.remove(save_path)
                saved_files.append(compressed_name)
                print(f"[✅] Compressed video: {compressed_name}")

            except FileNotFoundError:
                # 🧠 FFmpeg not found → keep original file
                print("[⚠️] FFmpeg not installed — skipping compression.")
                saved_files.append(temp_name)

            except subprocess.CalledProcessError:
                print(f"[❌] FFmpeg failed on {filename}")
                saved_files.append(temp_name)

        else:
            # 🖼️ Non-video → just save
            saved_files.append(temp_name)
            print(f"[📷] Saved image: {temp_name}")

    return jsonify({
        "message": f"✅ Uploaded {len(saved_files)} file(s) successfully.",
        "files": saved_files
    })


@app.route("/")
def home():
    """Serve main upload UI"""
    return send_from_directory("static", "index.html")


@app.route("/uploaded_files")
def uploaded_files():
    """List uploaded + compressed files"""
    html = "<h3>Uploaded Files</h3><ul>"
    for folder in ["static/uploads", "static/compressed"]:
        if os.path.exists(folder):
            for fname in os.listdir(folder):
                fpath = f"{folder}/{fname}"
                html += f'<li><a href="/{fpath}">{fname}</a></li>'
    html += "</ul>"
    return html


# 🚀 Start Flask app (for Railway)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ Server running on port {port}")
    app.run(host="0.0.0.0", port=port)
