import os
import traceback
from flask import Flask, request, jsonify
from clip_matcher import run_clip_match_test  # must exist in same folder

app = Flask(__name__)

# --- Root Health Check ---
@app.route("/", methods=["GET"])
def home():
    return "🟢 CLIP Test Server is running!"

# --- CLIP Match Test API ---
@app.route("/match", methods=["POST"])
def match_scope_to_images():
    try:
        # Expecting multipart/form-data:
        # scope_file: a .txt file
        # image_files: one or more image files
        scope_file = request.files.get("scope_file")
        image_files = request.files.getlist("image_files")

        if not scope_file or not image_files:
            return jsonify({
                "error": "Missing 'scope_file' or 'image_files' in upload"
            }), 400

        # --- Save uploaded files temporarily ---
        os.makedirs("/tmp/clip_test", exist_ok=True)
        scope_path = os.path.join("/tmp/clip_test", scope_file.filename)
        scope_file.save(scope_path)

        image_paths = []
        for img in image_files:
            img_path = os.path.join("/tmp/clip_test", img.filename)
            img.save(img_path)
            image_paths.append(img_path)

        print(f"🧠 [DEBUG] Scope saved to: {scope_path}")
        print(f"🧠 [DEBUG] {len(image_paths)} images uploaded.")
        print(f"🧠 [DEBUG] Running CLIP analysis...")

        # --- Run CLIP Matching ---
        results = run_clip_match_test(scope_path, image_paths)

        print(f"✅ [DEBUG] CLIP match completed successfully.")
        return jsonify({
            "status": "success",
            "results": results
        })

    except Exception as e:
        print("❌ [ERROR] CLIP match failed:")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# --- Optional Debug Endpoint ---
@app.route("/debug", methods=["GET"])
def debug_info():
    info = {
        "cwd": os.getcwd(),
        "files_in_tmp": os.listdir("/tmp") if os.path.exists("/tmp") else [],
        "env_vars": {k: v for k, v in os.environ.items() if "RAILWAY" in k or "PORT" in k}
    }
    return jsonify(info)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting CLIP Test Server on port {port} ...")
    app.run(debug=True, host="0.0.0.0", port=port)
