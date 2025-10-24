from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import datetime
from utils.pdf_generator import create_daily_log_pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'static/generated'

# Ensure necessary folders exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['GENERATED_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

@app.route("/")
def health_check():
    return "✅ Nails & Notes API is running and ready!"

@app.route("/form", methods=["GET"])
def form():
    return render_template("form.html")

@app.route("/generate_form", methods=["POST"])
def generate_form():
    try:
        data = request.form.to_dict()
        print("📝 Received form data:", data)

        # ---- Save uploaded images ----
        image_paths = []
        for img in request.files.getlist("images"):
            if img and img.filename:
                filename = secure_filename(img.filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img.save(img_path)
                image_paths.append(img_path)
                print(f"📸 Saved image: {img_path}")

        # ---- Save logo ----
        logo_path = None
        logo = request.files.get("logo")
        if logo and logo.filename:
            logo_filename = secure_filename(logo.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
            logo.save(logo_path)
            print(f"🏗️ Saved logo: {logo_path}")

        # ---- Save safety sheet ----
        safety_path = None
        safety = request.files.get("safety_sheet")
        if safety and safety.filename:
            safety_filename = secure_filename(safety.filename)
            safety_path = os.path.join(app.config['UPLOAD_FOLDER'], safety_filename)
            safety.save(safety_path)
            print(f"🦺 Saved safety sheet: {safety_path}")

        # ---- Optional AI & progress data ----
        ai_analysis = data.get("ai_analysis", "")
        progress_report = data.get("progress_report", "")

        # ---- Generate unique filename ----
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"DailyLog_{timestamp}.pdf"
        output_path = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
        print(f"📄 PDF will be saved at: {output_path}")

        # ---- Generate the PDF ----
        print("⚙️ Generating PDF...")
        create_daily_log_pdf(
            data=data,
            image_paths=image_paths,
            output_path=output_path,
            logo_path=logo_path,
            ai_analysis=ai_analysis,
            progress_report=progress_report,
            safety_path=safety_path
        )
        print(f"✅ PDF generated successfully: {output_path}")

        return jsonify({"pdf_url": f"/generated/{pdf_filename}"})

    except Exception as e:
        print("❌ Error during PDF generation:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/generated/<filename>")
def serve_generated_pdf(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True)
