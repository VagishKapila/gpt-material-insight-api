# ✅ Full updated `app.py` with detailed debuggers and consistent media ordering
import os
import uuid
import json
from flask import Flask, render_template, request, send_from_directory, redirect
from werkzeug.utils import secure_filename
from datetime import datetime
from utils.pdf_generator import create_daily_log_pdf
from utils.compare_scope_vs_log import analyze_scope_vs_log

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
SESSION_FOLDER = 'static/sessions'
SCOPE_FOLDER = 'static/scope'
LOGO_FOLDER = 'static/logos'
SAFETY_FOLDER = 'static/safety'

for folder in [UPLOAD_FOLDER, SESSION_FOLDER, SCOPE_FOLDER, LOGO_FOLDER, SAFETY_FOLDER]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def index():
    return redirect('/form')

@app.route('/form')
def form():
    return render_template('form.html', datetime=datetime)

@app.route('/generate_form', methods=['POST'])
def generate_form():
    session_id = str(uuid.uuid4())
    session_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    form_data = request.form.to_dict()
    media_items = []
    print("\n📥 Form Submission Received")
    print(f"Form Fields: {form_data}")

    files = request.files.getlist("media_files")
    print(f"🔍 Received {len(files)} media files")

    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1].lower()
            uid_filename = f"{session_id}_{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(UPLOAD_FOLDER, uid_filename)
            file.save(save_path)

            media_type = 'video' if ext in ['.mp4', '.mov', '.avi', '.webm'] else 'image'
            media_item = {'type': media_type, 'path': save_path.replace('static/', '')}

            if media_type == 'video':
                from utils.pdf_generator import generate_video_thumbnail
                thumb_path = generate_video_thumbnail(save_path)
                if thumb_path:
                    media_item['thumbnail'] = thumb_path.replace('static/', '')

            media_items.append(media_item)
            print(f"✅ Saved {media_type.upper()}: {media_item}")

    logo_path = None
    if 'logo' in request.files and request.files['logo'].filename:
        logo_file = request.files['logo']
        ext = os.path.splitext(logo_file.filename)[1]
        logo_path = os.path.join(LOGO_FOLDER, f"{session_id}{ext}")
        logo_file.save(logo_path)
        print(f"🖼️ Logo saved: {logo_path}")

    scope_path = None
    if 'scope_doc' in request.files and request.files['scope_doc'].filename:
        scope_file = request.files['scope_doc']
        ext = os.path.splitext(scope_file.filename)[1]
        scope_path = os.path.join(SCOPE_FOLDER, f"{session_id}{ext}")
        scope_file.save(scope_path)
        print(f"📄 Scope of Work saved: {scope_path}")

    safety_path = None
    if 'safety_sheet' in request.files and request.files['safety_sheet'].filename:
        safety_file = request.files['safety_sheet']
        ext = os.path.splitext(safety_file.filename)[1]
        safety_path = os.path.join(SAFETY_FOLDER, f"{session_id}{ext}")
        safety_file.save(safety_path)
        print(f"🛡️ Safety Sheet saved: {safety_path}")

    session_data = {
        'form_data': form_data,
        'media_items': media_items,
        'logo_path': logo_path,
        'scope_path': scope_path,
        'safety_path': safety_path
    }
    with open(session_path, 'w') as f:
        json.dump(session_data, f)
        print(f"💾 Session data saved: {session_path}")

    return render_template('preview.html',
                           form_data=form_data,
                           media_items=media_items,
                           session_id=session_id)

@app.route('/submit_preview', methods=['POST'])
def submit_preview():
    session_id = request.form.get('session_id')
    session_path = os.path.join(SESSION_FOLDER, f"{session_id}.json")

    if not os.path.exists(session_path):
        return "Session not found", 404

    with open(session_path, 'r') as f:
        session = json.load(f)

    form_data = session.get('form_data', {})
    media_items = session.get('media_items', [])
    image_paths = ["static/" + item['path'] for item in media_items if item['type'] == 'image']
    video_paths = ["static/" + item['path'] for item in media_items if item['type'] == 'video']

    logo_path = session.get('logo_path')
    scope_path = session.get('scope_path')
    safety_path = session.get('safety_path')

    ai_result = None
    if form_data.get('enable_ai') and scope_path:
        ai_result = analyze_scope_vs_log(scope_path, form_data, image_paths)
        print("🤖 AI Match Results:", ai_result)

    from utils.weather_icon import get_weather_icon
    weather_icon = get_weather_icon(form_data.get("weather"))

    output_pdf = os.path.join("static/generated", f"{session_id}.pdf")
    os.makedirs("static/generated", exist_ok=True)

    create_daily_log_pdf(
        data=form_data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=ai_result,
        progress_report=None,
        save_path=output_pdf,
        weather_icon_path=weather_icon,
        safety_sheet_path=safety_path
    )

    return redirect("/" + output_pdf)

if __name__ == '__main__':
    app.run(debug=True)
