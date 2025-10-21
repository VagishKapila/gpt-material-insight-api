from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime
import os
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Rebuild trigger - 10/21
# ROUTE: Health check root
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

# ROUTE: Optional form (only needed if you use a form.html template)
@app.route("/form")
def form_page():
    return render_template("form.html")

# ROUTE: Generate dummy PDF (testing only)
@app.route("/generate-test-pdf", methods=["GET"])
def generate_test_pdf():
    output_dir = os.path.join("static", "generated")
    os.makedirs(output_dir, exist_ok=True)
    test_pdf_path = os.path.join(output_dir, "test_upload.pdf")
    
    with open(test_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n% Dummy test PDF\n%%EOF")
    
    return jsonify({
        "message": "✅ Test PDF created",
        "pdf_url": "/generated/test_upload.pdf"
    })

# ROUTE: Ping test
@app.route("/ping")
def ping():
    return "PONG"
    
# RUN LOCALLY (not used on Render)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
