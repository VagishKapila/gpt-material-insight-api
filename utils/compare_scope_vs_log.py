import os
import re
import numpy as np
from fuzzywuzzy import fuzz
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

SCOPE_DIR = "static/scope"  # Match app.py
EXCLUSION_PHRASES = [
    "no ", "not ", "do not", "does not", "will not", "excluded", "without",
    "doesn't", "isn't", "wasn't", "aren't", "weren't", "cannot", "never"
]

model = SentenceTransformer('all-MiniLM-L6-v2')


def clean_scope_text(text):
    text = re.sub(r"[^\x00-\x7F]+", "", text).strip()
    if len(text) < 5:
        return ""
    if text.lower().startswith((
        "client", "project", "date", "prepared by", "include", "scope", "description", "location"
    )):
        return ""
    if any(phrase in text.lower() for phrase in EXCLUSION_PHRASES):
        return ""
    return text


def load_scope_for_project(project_id):
    scope_path = os.path.join(SCOPE_DIR, f"{project_id}.txt")  # Match app.py naming
    if not os.path.exists(scope_path):
        return []
    with open(scope_path, "r", encoding="utf-8") as f:
        return [clean_scope_text(line) for line in f.readlines() if clean_scope_text(line)]


def analyze_scope_vs_log(scope_items, daily_log_text, threshold=0.65):
    """
    Compare scope items vs full daily log text (merged)
    """
    if not scope_items or not daily_log_text:
        return {
            "completion": 0,
            "scored_items": [],
            "out_of_scope": ["⚠️ Missing scope items or log data."]
        }

    log_embedding = model.encode([daily_log_text])[0].reshape(1, -1)
    scope_embeddings = model.encode(scope_items)

    matched = 0
    scored_items = []

    for item, scope_embed in zip(scope_items, scope_embeddings):
        scope_embed_2d = np.array(scope_embed).reshape(1, -1)
        cosine_score = cosine_similarity(scope_embed_2d, log_embedding)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), daily_log_text.lower()) / 100
        final_score = max(cosine_score, fuzzy_score)
        is_match = final_score >= threshold

        if is_match:
            matched += 1

        scored_items.append({
            "scope": item,
            "confidence": round(final_score * 100, 1),
            "match": is_match
        })

    # Smarter out-of-scope logic
    known_ignore = ["ppe", "tailgate", "safety", "meeting"]
    log_lines = [line.strip() for line in daily_log_text.split("\n") if line.strip()]
    out_of_scope = []
    for line in log_lines:
        if any(kw in line.lower() for kw in known_ignore):
            continue
        if all(fuzz.partial_ratio(line.lower(), item.lower()) < 60 for item in scope_items):
            out_of_scope.append(line)

    percent_complete = round((matched / len(scope_items)) * 100, 1) if scope_items else 0
    return {
        "completion": percent_complete,
        "scored_items": scored_items,
        "out_of_scope": out_of_scope[:10]
    }


def parse_scope_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
        doc.close()
        return text

    elif ext == ".docx":
        from docx import Document
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    elif ext in [".xls", ".xlsx"]:
        import pandas as pd
        df = pd.read_excel(file_path, engine="openpyxl")
        return df.to_string(index=False)

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        return "Unsupported file format"
