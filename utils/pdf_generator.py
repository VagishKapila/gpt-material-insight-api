# ✅ UPDATED `pdf_generator.py`
# Includes:
# - Page 1: Daily Log
# - Page 2: Photos (2-column layout)
# - Page 3: AI Analysis + Scope Progress
# - Uses user logo (optional)

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from datetime import datetime
from PyPDF2 import PdfReader
import docx
import json


# Utility: Extract text from PDF/DOCX for Scope

def extract_text_from_scope(scope_path):
    if scope_path.endswith(".pdf"):
        with open(scope_path, "rb") as f:
            reader = PdfReader(f)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif scope_path.endswith(".docx"):
        doc = docx.Document(scope_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return ""


def generate_scope_progress(scope_tasks, work_done):
    completed, in_progress, not_started = [], [], []
    work_text = work_done.lower()

    for task in scope_tasks:
        task_lower = task.lower()
        if task_lower in work_text:
            completed.append(task)
        elif any(word in work_text for word in task_lower.split()[:3]):
            in_progress.append(task)
        else:
            not_started.append(task)

    return completed, in_progress, not_started


def parse_scope_tasks(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = [line[2:] if line[:2] in ("- ", "• ") else line for line in lines]
    return bullets


# Main PDF Generator

def create_daily_log_pdf(data, photo_paths, logo_path=None, ai_analysis_text="", scope_progress_text="", output_path="daily_log.pdf"):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("<b>🛠️ DAILY LOG</b>", styles['Title']))
    story.append(Spacer(1, 12))

    if logo_path:
        try:
            img = Image(logo_path, width=100, height=40)
            story.append(img)
        except:
            pass

    # Section 1: Metadata
    for field in ["project_name", "location", "date", "weather"]:
        label = field.replace("_", " ").title()
        story.append(Paragraph(f"<b>{label}:</b> {data.get(field, '')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Section 2: Notes
    for field in ["crew_notes", "work_done", "safety_notes"]:
        label = field.replace("_", " ").title()
        story.append(Paragraph(f"<b>{label}</b>", styles['Heading4']))
        story.append(Paragraph(data.get(field, ""), styles['Normal']))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Powered by Nails & Notes</i>", styles['Normal']))
    doc.build(story)

    # Page 2: Job Site Photos
    c = canvas.Canvas(output_path, pagesize=A4)
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "📸 Job Site Photos")

    x, y = 40, 750
    for i, path in enumerate(photo_paths[:20]):
        try:
            img = ImageReader(path)
            c.drawImage(img, x, y, width=240, height=180, preserveAspectRatio=True)
            x += 270
            if x > 500:
                x = 40
                y -= 200
                if y < 100:
                    c.showPage()
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(40, 800, "📸 Job Site Photos (Cont.)")
                    y = 750
        except:
            continue

    # Page 3: AI + Scope Progress
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "🤖 AI/AR Analysis")
    c.setFont("Helvetica", 12)
    text_obj = c.beginText(40, 780)
    for line in ai_analysis_text.splitlines():
        text_obj.textLine(line)
    c.drawText(text_obj)

    if scope_progress_text:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, 600, "📋 Scope Progress Tracker")
        c.setFont("Helvetica", 12)
        y = 580
        for line in scope_progress_text.splitlines():
            if y < 60:
                c.showPage()
                y = 800
            c.drawString(40, y, line)
            y -= 16

    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(A4[0]/2, 30, "Confidential – Do Not Duplicate without written consent from BAINS Dev Comm")
    c.save()

    return output_path
