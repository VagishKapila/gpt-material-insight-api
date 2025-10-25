# compare_scope_vs_log.py

import os
import json
from difflib import SequenceMatcher
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------- CONFIG ----------
SCOPE_CACHE_FOLDER = "scope_cache"
SIMILARITY_THRESHOLD = 0.5  # Cosine similarity threshold

# ---------- HELPERS ----------
def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def load_scope_for_project(project_id: str) -> List[str]:
    path = os.path.join(SCOPE_CACHE_FOLDER, f"{project_id}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_scope_for_project(project_id: str, scope_items: List[str]):
    os.makedirs(SCOPE_CACHE_FOLDER, exist_ok=True)
    path = os.path.join(SCOPE_CACHE_FOLDER, f"{project_id}.json")
    with open(path, "w") as f:
        json.dump(scope_items, f, indent=2)

def extract_scope_items(raw_text: str) -> List[str]:
    lines = [line.strip() for line in raw_text.split("\n") if len(line.strip()) > 15]
    return lines

# ---------- MAIN COMPARISON ----------
def analyze_scope_vs_log(scope_items: List[str], work_done: str, crew_notes: str, safety_notes: str) -> Dict:
    full_log = "\n".join([work_done, crew_notes, safety_notes]).strip()
    if not scope_items or not full_log:
        return {
            "completion": 0,
            "matched": [],
            "unmatched": scope_items,
            "out_of_scope": [],
            "change_order_suggestions": ["Scope or daily log is empty. No valid comparison made."]
        }

    vectorizer = TfidfVectorizer().fit(scope_items + [full_log])
    scope_vecs = vectorizer.transform(scope_items)
    log_vec = vectorizer.transform([full_log])

    matched = []
    unmatched = []

    for i, scope in enumerate(scope_items):
        score = cosine_similarity(scope_vecs[i], log_vec)[0][0]
        if score >= SIMILARITY_THRESHOLD:
            matched.append(scope)
        else:
            unmatched.append(scope)

    out_of_scope = []
    for line in full_log.split("\n"):
        if not any(similar(line, s) > 0.5 for s in scope_items):
            out_of_scope.append(line.strip())

    completion = round(100 * len(matched) / max(1, len(scope_items)))

    return {
        "completion": completion,
        "matched": matched,
        "unmatched": unmatched,
        "out_of_scope": out_of_scope[:10],
        "change_order_suggestions": [
            f"Suggest review of {len(out_of_scope)} possible out-of-scope items."
        ] if out_of_scope else []
    }
