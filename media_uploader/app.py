from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
COMPRESSED_FOLDER = 'static/compressed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPRESSED_FOLDER, exist_ok=True)

@app.route("/upload_media_test", methods=["POST"])
def upload_media():
    uploaded_files = request.files.getlist("media_files")
    saved_files = []

    for f in uploaded_files:
        filename = secure_filename(f.filename)
        file_ext = filename.rsplit('.', 1)[-1].lower()
        temp_name = f"{uuid.uuid4().hex}.{file_ext}"
        save_path = os.path.join(UPLOAD_FOLDER, temp_name)
        f.save(save_path)

        # If it's a video, compress it
        if file_ext in ["mp4", "mov", "avi", "mkv"]:
            compressed_name = f"compressed_{temp_name}"
            compressed_path = os.path.join(COMPRESSED_FOLDER, compressed_name)

            ffmpeg_cmd = [
                "ffmpeg", "-i", save_path,
                "-vcodec", "libx264", "-crf", "28",
                "-preset", "veryfast",  # Speed vs quality trade-off
                "-y",  # Overwrite output if exists
                compressed_path
            ]

            try:
                subprocess.run(ffmpeg_cmd, check=True)
                os.remove(save_path)  # Cleanup original
                saved_files.append(compressed_name)
            except subprocess.CalledProcessError:
                saved_files.append(f"⚠️ Compression failed: {filename}")
        else:
            saved_files.append(temp_name)

    return jsonify({
        "message": f"✅ Uploaded {len(saved_files)} file(s) successfully.",
        "files": saved_files
    })


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


# ✅ Add this to explicitly start Flask in Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Railway uses dynamic ports
    app.run(host="0.0.0.0", port=port)
