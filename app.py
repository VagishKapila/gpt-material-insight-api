# app.py – Phase 3C: Add/Delete Jobsite Photos + Validation + Logging

import os
import uuid
import traceback
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import json
from utils.pdf_generator import create_daily_log_pdf
from utils.scope_parser import parse_scope_file
from utils.compare_scope_vs_log import analyze_scope_vs_log

UPLOAD_FOLDER = 'static/uploads'
SESSION_FOLDER = 'session_data'
GENERATED_FOLDER = 'static/generated'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SESSION_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_session_data(session_id):
    try:
        with open(f'{SESSION_FOLDER}/{session_id}.json', 'r') as f:
            return json.load(f)
    except:
        return {}


def save_session_data(session_id, data):
    with open(f'{SESSION_FOLDER}/{session_id}.json', 'w') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def index():
    return "✅ Server is running. Use /form to submit Daily Logs."


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/generate_form', methods=['POST'])
def generate_form():
    try:
        session_id = str(uuid.uuid4())
        form_data = request.form.to_dict()
        image_paths = []

        # Save images
        if 'images' in request.files:
            for file in request.files.getlist('images'):
                if file and allowed_file(file.filename):
                    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    image_paths.append(file_path)

        # Save scope
        scope_file = request.files.get('scope_doc')
        scope_path = None
        if scope_file:
            scope_path = os.path.join(UPLOAD_FOLDER, secure_filename(scope_file.filename))
            scope_file.save(scope_path)

        # Save safety sheet
        safety_sheet = request.files.get('safety_sheet')
        safety_sheet_path = None
        if safety_sheet:
            safety_sheet_path = os.path.join(UPLOAD_FOLDER, secure_filename(safety_sheet.filename))
            safety_sheet.save(safety_sheet_path)

        session_data = {
            "form_data": form_data,
            "image_paths": image_paths,
            "scope_path": scope_path,
            "safety_sheet_path": safety_sheet_path,
            "ai_results": {}
        }
        save_session_data(session_id, session_data)
        return redirect(url_for('preview', session_id=session_id))

    except Exception as e:
        print("❌ Error in generate_form:", e)
        traceback.print_exc()
        return "Form processing error."


@app.route('/preview/<session_id>')
def preview(session_id):
    try:
        session_data = get_session_data(session_id)
        return render_template(
            'preview.html',
            session_id=session_id,
            form_data=session_data.get('form_data', {}),
            image_paths=session_data.get('image_paths', []),
            ai_results=session_data.get('ai_results', {}),
            safety_sheet_path=session_data.get('safety_sheet_path', None)
        )
    except Exception as e:
        print("❌ Error in preview:", e)
        traceback.print_exc()
        return "Preview failed."


@app.route('/add_image/<session_id>', methods=['POST'])
def add_image(session_id):
    try:
        file = request.files.get('new_image')
        if not file or not allowed_file(file.filename):
            return redirect(url_for('preview', session_id=session_id))

        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        data = get_session_data(session_id)
        data.setdefault("image_paths", []).append(path)
        save_session_data(session_id, data)

        return redirect(url_for('preview', session_id=session_id))
    except Exception as e:
        print("❌ Error in add_image:", e)
        traceback.print_exc()
        return "Failed to add image."


@app.route('/remove_image/<session_id>', methods=['POST'])
def remove_image(session_id):
    try:
        filename = request.form.get('remove_image')
        full_path = os.path.join(UPLOAD_FOLDER, filename)

        data = get_session_data(session_id)
        data["image_paths"] = [p for p in data.get("image_paths", []) if os.path.basename(p) != filename]
        save_session_data(session_id, data)

        if os.path.exists(full_path):
            os.remove(full_path)

        return redirect(url_for('preview', session_id=session_id))
    except Exception as e:
        print("❌ Error in remove_image:", e)
        traceback.print_exc()
        return "Failed to remove image."


@app.route('/submit_preview', methods=['POST'])
def submit_preview():
    try:
        session_id = request.form.get("session_id")
        data = get_session_data(session_id)
        total_items = int(request.form.get("total_items", 0))
        scored_items = []

        for i in range(total_items):
            scored_items.append({
                "scope": request.form.get(f"scope_{i}"),
                "confidence": int(request.form.get(f"confidence_{i}")),
                "match": request.form.get(f"match_{i}") == "on",
                "matched_image": request.form.get(f"matched_image_{i}")
            })

        completion = sum(item["confidence"] for item in scored_items if item["match"]) / max(1, total_items)
        data["ai_results"] = {
            "completion": round(completion),
            "scored_items": scored_items,
            "out_of_scope": data.get("ai_results", {}).get("out_of_scope", [])
        }

        output_path = os.path.join(GENERATED_FOLDER, f"{session_id}_daily_log.pdf")
        create_daily_log_pdf(
            data["form_data"],
            data["image_paths"],
            None,
            data["ai_results"],
            None,
            output_path,
            None,
            data.get("safety_sheet_path")
        )
        return send_from_directory(GENERATED_FOLDER, os.path.basename(output_path), as_attachment=True)

    except Exception as e:
        print("❌ Error in submit_preview:", e)
        traceback.print_exc()
        return "PDF generation failed."


@app.route('/analyze_scope/<session_id>')
def analyze_scope(session_id):
    try:
        data = get_session_data(session_id)
        results = analyze_scope_vs_log(
            data.get("scope_path"),
            data.get("form_data"),
            data.get("image_paths", [])
        )
        data["ai_results"] = results
        save_session_data(session_id, data)
        return redirect(url_for("preview", session_id=session_id))
    except Exception as e:
        print("❌ Error in analyze_scope:", e)
        traceback.print_exc()
        return "Scope analysis failed."


if __name__ == '__main__':
    app.run(debug=True)
