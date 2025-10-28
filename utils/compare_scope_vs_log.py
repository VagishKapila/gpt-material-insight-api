import os
import re
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz

SCOPE_DIR = "scope"
EXCLUSION_PHRASES = [
    "no ", "not ", "do not", "does not", "will not", "excluded", "without",
    "doesn't", "isn't", "wasn't", "aren't", "weren't", "cannot", "never"
]

# Load sentence transformer model once
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight + fast

def clean_scope_text(text):
    """Cleans and filters scope lines."""
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
    """Loads scope from saved .txt file for given project ID."""
    scope_path = os.path.join(SCOPE_DIR, f"scope_{project_id}.txt")
    if not os.path.exists(scope_path):
        return []
    with open(scope_path, "r", encoding="utf-8") as f:
        return [clean_scope_text(line) for line in f.readlines() if clean_scope_text(line)]

def analyze_scope_vs_log(scope_items, daily_log_data, threshold=0.65):
    """
    Compares log entries against scope using sentence embeddings + fuzzy matching.
    Returns:
        - completion %,
        - scored match items,
        - out-of-scope detections.
    """
    work_done = daily_log_data.get("work_done", "")
    crew_notes = daily_log_data.get("crew_notes", "")
    safety_notes = daily_log_data.get("safety_notes", "")
    full_log = f"{work_done}\n{crew_notes}\n{safety_notes}".strip()

    if not scope_items or not full_log:
        return {
            "completion": 0,
            "scored_items": [],
            "out_of_scope": ["⚠️ Missing scope items or log data."]
        }

    # ✅ FIX: encode full_log as list to get 2D embedding
    log_embedding = model.encode([full_log])
    scope_embeddings = model.encode(scope_items)

    matched = 0
    scored_items = []

    for item, scope_embed in zip(scope_items, scope_embeddings):
        # All arrays are now 2D: [1, 384]
        cosine_score = cosine_similarity([scope_embed], log_embedding)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), full_log.lower()) / 100
        final_score = max(cosine_score, fuzzy_score)
        is_match = final_score >= threshold

        if is_match:
            matched += 1

        scored_items.append({
            "scope": item,
            "confidence": round(final_score * 100, 1),
            "match": is_match
        })

    # 🔎 Out-of-Scope Detection (text lines not matching any scope item)
    known_ignore = ["ppe", "tailgate", "safety", "meeting"]
    log_lines = [line.strip() for line in full_log.split("\n") if line.strip()]
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
    """Parses uploaded scope file in .pdf, .docx, .xlsx, or .txt formats."""
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
