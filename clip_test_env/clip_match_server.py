import os
import json
from flask import Flask, request, jsonify
from clip_matcher import run_clip_match_test

app = Flask(__name__)

@app.route("/")
def health():
    return "✅ CLIP Matcher Server is running!"

@app.route("/debug_env")
def debug_env():
    return jsonify({
        "cwd": os.getcwd(),
        "files": os.listdir(),
        "python_version": os.sys.version,
        "env": dict(os.environ)
    })

@app.route("/run_test", methods=["POST"])
def run_test():
    try:
        data = request.get_json()
        scope_file = data.get("scope_file")
        image_files = data.get("image_files", [])

        if not scope_file or not image_files:
            return jsonify({"error": "Missing 'scope_file' or 'image_files' in request"}), 400

        result = run_clip_match_test(scope_file, image_files)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=True, host="0.0.0.0", port=port)
