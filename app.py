from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime
import os

app = Flask(__name__, static_folder="static", static_url_path="/static")

# ROUTE: Health check
@app.route("/")
def index():
    return "✅ Daily Log AI is running"

# ROUTE: Serve PDF files from /static/generated
@app.route("/generated/<filename>")
def serve_pdf(filename):
    try:
        return send_from_directory("static/generated", filename)
    except FileNotFoundError:
        return "PDF not found", 404

# ROUTE: Form page (optional, can delete if not using)
@app.route("/form")
def form_page():
    return render_template("form.html")  # Only if using templates

# ROUTE: Generate dummy PDF (for test purposes only)
@app.route("/generate-test-pdf", methods=["GET"])
def generate_test_pdf():
    test_pdf_path = os.path.join("static/generated", "test_upload.pdf")
    if not os.path.exists("static/generated"):
        os.makedirs("static/generated")
    with open(test_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n% Dummy test PDF\n%%EOF")
    return jsonify({
        "message": "Test PDF created successfully",
        "pdf_url": f"/generated/test_upload.pdf"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
