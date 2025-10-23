import json
import os
import re
from PyPDF2 import PdfReader
import docx

SCOPE_FOLDER = "static/scopes"
os.makedirs(SCOPE_FOLDER, exist_ok=True)

def extract_scope_text(scope_path):
    """Extract raw text from PDF or DOCX"""
    text = ""
    if scope_path.endswith(".pdf"):
        with open(scope_path, "rb") as f:
            reader = PdfReader(f)
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
    elif scope_path.endswith(".docx"):
        doc = docx.Document(scope_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    else:
        with open(scope_path, "r", errors="ignore") as f:
            text = f.read()
    return text

def extract_scope_tasks(scope_text):
    """Split scope text into clean task lines"""
    lines = [line.strip() for line in scope_text.splitlines() if line.strip()]
    return [re.sub(r"^[•\-0-9\.\)\s]+", "", line) for line in lines]

def save_project_scope(project_id, scope_tasks):
    path = os.path.join(SCOPE_FOLDER, f"{project_id}_scope.json")
    with open(path, "w") as f:
        json.dump(scope_tasks, f)

def load_project_scope(project_id):
    path = os.path.join(SCOPE_FOLDER, f"{project_id}_scope.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def compare_scope_to_daily_log(scope_tasks, work_done):
    """Match work done text against scope tasks"""
    work = work_done.lower()
    completed, pending = [], []
    for task in scope_tasks:
        if task.lower() in work:
            completed.append(task)
        else:
            pending.append(task)
    return {"completed": completed, "pending": pending}

def format_progress_report(progress):
    """Return formatted multi-line report"""
    report = ["Scope Progress Summary:"]
    report.append(f"Completed ({len(progress['completed'])}):")
    for t in progress["completed"]:
        report.append(f"  ✅ {t}")
    report.append(f"\nPending ({len(progress['pending'])}):")
    for t in progress["pending"]:
        report.append(f"  ⏳ {t}")
    return "\n".join(report)
