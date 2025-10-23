from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image as PILImage
import os

def add_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawString(40, 20, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
    canvas_obj.drawRightString(570, 20, f"Page {doc.page}")
    canvas_obj.restoreState()

def create_daily_log_pdf(data, image_paths, logo_path=None, ai_analysis=None, scope_progress=None, save_path="output.pdf", safety_path=None):
    temp_pdf = "temp_main.pdf"
    doc = SimpleDocTemplate(temp_pdf, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title_style = styles["Heading1"]

    # Header + Logo
    if logo_path and os.path.exists(logo_path):
        img = PILImage.open(logo_path)
        img.thumbnail((100, 100))
        img.save("temp_logo.png")
        logo = Image("temp_logo.png", width=60, height=60)
        elements.append(logo)

    elements.append(Paragraph("DAILY LOG", title_style))
    elements.append(Spacer(1, 12))

    def colored_label(label): return f'<font color="blue"><b>{label}:</b></font>'

    # Key Info
    for field in ["date", "location", "crew_notes", "work_done", "safety_notes", "weather", "equipment_used"]:
        label = field.replace("_", " ").title()
        value = data.get(field, "—")
        elements.append(Paragraph(f"{colored_label(label)} {value}", normal))
        elements.append(Spacer(1, 6))

    elements.append(PageBreak())

    # PAGE 2 — PHOTOS
    elements.append(Paragraph("📸 Job Site Photos", title_style))
    elements.append(Spacer(1, 12))
    img_width = 250
    img_height = 180
    row = []

    for i, img_path in enumerate(image_paths):
        try:
            img = PILImage.open(img_path)
            img = img.convert('RGB')
            if img.width > img.height:
                img = img.rotate(270, expand=True)
            img.thumbnail((img_width, img_height))
            temp_name = f"temp_img_{i}.jpg"
            img.save(temp_name)
            row.append(Image(temp_name, width=img_width, height=img_height))
            if len(row) == 2:
                elements.extend(row)
                elements.append(Spacer(1, 12))
                row = []
        except:
            continue
    if row:
        elements.extend(row)
        elements.append(Spacer(1, 12))

    elements.append(PageBreak())

    # PAGE 3 — AI/Scope Analysis
    elements.append(Paragraph("🤖 AI + Scope Progress Analysis", title_style))
    elements.append(Spacer(1, 12))
    if ai_analysis:
        elements.append(Paragraph(f"{colored_label('AI Image Analysis')} {ai_analysis}", normal))
        elements.append(Spacer(1, 12))
    if scope_progress:
        elements.append(Paragraph(f"{colored_label('Scope Progress')} {scope_progress}", normal))
    elements.append(PageBreak())

    # PAGE 4 — Safety Upload
    if safety_path:
        elements.append(Paragraph("🛡️ Safety Sheet Upload", title_style))
        elements.append(Spacer(1, 12))
        if safety_path.lower().endswith(".pdf"):
            doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
            merger = PdfMerger()
            merger.append(temp_pdf)
            merger.append(safety_path)
            merger.write(save_path)
            merger.close()
            os.remove(temp_pdf)
            return
        else:
            try:
                img = PILImage.open(safety_path)
                if img.width > img.height:
                    img = img.rotate(270, expand=True)
                img.thumbnail((500, 650))
                img.save("temp_safety.jpg")
                elements.append(Image("temp_safety.jpg", width=400, height=500))
            except:
                elements.append(Paragraph("⚠️ Error displaying safety image.", normal))

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)

    # Clean up temp
    for f in os.listdir():
        if f.startswith("temp_"):
            try:
                os.remove(f)
            except:
                pass
