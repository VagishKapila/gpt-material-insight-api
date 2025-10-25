# app.py
from flask import Flask, render_template, request, send_from_directory
import os
import uuid
from utils.pdf_generator import create_daily_log_pdf  # ✅ Still using utils folder
from utils.helpers import get_weather_icon, fix_image_orientation

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
GENERATED_FOLDER = 'static/generated'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return "Nails & Notes API is live."

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/generate_form', methods=['POST'])
def generate_form():
    form_data = request.form.to_dict()

    images = request.files.getlist('images')
    logo = request.files.get('logo')
    scope_doc = request.files.get('scope_doc')
    safety_sheet = request.files.get('safety_sheet')

    enable_ai = form_data.get('enable_ai', 'on') == 'on'
    weather_icon_path = get_weather_icon(form_data.get("weather", ""))

    image_paths = []
    for img in images:
        if img:
            filename = f"{uuid.uuid4()}.jpg"
            path = os.path.join(UPLOAD_FOLDER, filename)
            img.save(path)
            fix_image_orientation(path)
            image_paths.append(path)

    logo_path = None
    if logo:
        filename = f"logo_{uuid.uuid4()}.png"
        logo_path = os.path.join(UPLOAD_FOLDER, filename)
        logo.save(logo_path)

    safety_path = None
    if safety_sheet:
        filename = f"safety_{uuid.uuid4()}_{safety_sheet.filename}"
        safety_path = os.path.join(UPLOAD_FOLDER, filename)
        safety_sheet.save(safety_path)

    save_filename = f"log_{uuid.uuid4()}.pdf"
    save_path = os.path.join(GENERATED_FOLDER, save_filename)

    create_daily_log_pdf(
        data=form_data,
        image_paths=image_paths,
        logo_path=logo_path,
        ai_analysis=enable_ai,
        progress_report=form_data.get("progress_report", ""),
        save_path=save_path,
        weather_icon_path=weather_icon_path,
        safety_sheet_path=safety_path
    )

    return {"pdf_url": f"/generated/{save_filename}"}

@app.route('/generated/<filename>')
def serve_generated(filename):
    return send_from_directory(GENERATED_FOLDER, filename)

# utils/pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


def create_daily_log_pdf(data, image_paths, logo_path, ai_analysis, progress_report, save_path, weather_icon_path, safety_sheet_path):
    doc = SimpleDocTemplate(save_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Logo
    if logo_path:
        elements.append(Image(logo_path, width=100, height=50))
        elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("DAILY LOG", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    # Weather
    if weather_icon_path:
        elements.append(Image(weather_icon_path, width=50, height=50))
        elements.append(Spacer(1, 0.2 * inch))

    # Daily Log Metadata
    for k, v in data.items():
        if k not in ["enable_ai", "progress_report"]:
            elements.append(Paragraph(f"<b>{k}:</b> {v}", styles['Normal']))

    elements.append(PageBreak())

    # Page 2 – Job Site Photos
    for path in image_paths:
        elements.append(Image(path, width=5*inch, height=3*inch))
        elements.append(Spacer(1, 0.2 * inch))
    elements.append(PageBreak())

    # Page 3 – AI / AR
    if ai_analysis or progress_report:
        elements.append(Paragraph("AI / AR COMPARISON", styles['Title']))
        elements.append(Spacer(1, 0.2 * inch))

        if isinstance(ai_analysis, bool):
            ai_text = "Enabled" if ai_analysis else "Disabled"
        else:
            ai_text = str(ai_analysis)

        elements.append(Paragraph("<b>AI Analysis:</b>", styles['Heading3']))
        elements.append(Paragraph(ai_text, styles['Normal']))

        if progress_report:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("<b>Scope Progress:</b>", styles['Heading3']))
            elements.append(Paragraph(progress_report, styles['Normal']))

        elements.append(PageBreak())

    # Page 4 – Safety Sheet
    if safety_sheet_path:
        elements.append(Paragraph("Safety Sheet", styles['Title']))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Image(safety_sheet_path, width=5*inch, height=3*inch))

    doc.build(elements)
