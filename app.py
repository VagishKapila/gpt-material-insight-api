from flask import Flask, request, send_from_directory, render_template, jsonify
import os
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'generated')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        # Handle uploaded files and inputs here (placeholder)
        # You can expand this as needed to read form data

        # For now, generate a dummy PDF file
        filename = "output.pdf"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, "wb") as f:
            f.write(b"%PDF-1.4 dummy content")

        return jsonify({"success": True, "pdf_url": f"/static/generated/{filename}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/static/generated/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
