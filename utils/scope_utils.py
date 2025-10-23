import os
import re
import json
from difflib import SequenceMatcher
from docx import Document
from PyPDF2 import PdfReader

# --- Extract text from uploaded Scope of Work ---
def extract_scope_text(scope_path):
    text = ""
    if not os.path.exists(scope_path):
        return text

    ext = os.path.splitext(scope_path)[1].lower()

    try:
        if ext == ".pdf":
            reader = PdfReader(scope_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif ext in [".doc", ".docx"]:
            doc = Document(scope_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            with open(scope_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
    except Exception as e:
        text = f"Error extracting scope: {e}"

    return text.strip()


# --- Compare scope with daily log (AI-style fuzzy matching) ---
def analyze_scope_progress(scope_text, log_text):
    if not scope_text or not log_text:
        return []

    scope_lines = [
        line.strip()
        for line in scope_text.splitlines()
        if 5 < len(line.strip()) < 200
    ]

    log_lines = log_text.lower()
    report = []

    for line in scope_lines:
        clean_line = re.sub(r"[^a-zA-Z0-9\s]", "", line.lower())
        match_score = SequenceMatcher(None, clean_line, log_lines).ratio()

        # Logic for progress
        if match_score > 0.6:
            status = "done"
        elif 0.3 < match_score <= 0.6:
            status = "in-progress"
        else:
            status = "pending"

        report.append({
            "task": line[:100] + ("..." if len(line) > 100 else ""),
            "status": status
        })

    return report


# --- Optional helper to save AI report ---
def save_progress_report(project_name, report, output_dir="static/progress_tracking"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{project_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return file_path
