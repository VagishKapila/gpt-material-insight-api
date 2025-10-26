# utils/compare_scope_vs_log.py
import os
import json
from difflib import SequenceMatcher
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------- CONFIG ----------
SCOPE_CACHE_FOLDER = "scope_cache"
SIMILARITY_THRESHOLD = 0.5   # can tune later

# ---------- HELPERS ----------
def similar(a: str, b: str) -> float:
    """Basic fuzzy string ratio."""
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
    """Split scope text into meaningful lines (ignore very short ones)."""
    return [line.strip() for line in raw_text.split("\n") if len(line.strip()) > 15]

# ---------- MAIN COMPARISON ----------
def analyze_scope_vs_log(scope_items: List[str],
                         work_done: str,
                         crew_notes: str,
                         safety_notes: str) -> Dict:
    """
    Compare scope items with daily log entries and return detailed confidence data.
    """
    full_log = "\n".join([work_done, crew_notes, safety_notes]).strip()
    if not scope_items or not full_log:
        return {
            "completion": 0,
            "scored_items": [],
            "matched": [],
            "unmatched": scope_items,
            "out_of_scope": [],
            "change_order_suggestions": ["Scope or daily log is empty. No valid comparison made."]
        }

    # TF‑IDF vectorization for similarity
    vectorizer = TfidfVectorizer().fit(scope_items + [full_log])
    scope_vecs = vectorizer.transform(scope_items)
    log_vec = vectorizer.transform([full_log])

    scored_items = []
    matched, unmatched = [], []

    for i, scope in enumerate(scope_items):
        score = cosine_similarity(scope_vecs[i], log_vec)[0][0]
        fuzzy = similar(scope, full_log)
        confidence = round((score * 0.8 + fuzzy * 0.2), 3)  # blended confidence

        match = confidence >= SIMILARITY_THRESHOLD
        scored_items.append({
            "scope": scope,
            "confidence": confidence,
            "match": match
        })
        if match:
            matched.append(scope)
        else:
            unmatched.append(scope)

    # Out‑of‑scope lines
    out_of_scope = []
    for line in full_log.split("\n"):
        if not any(similar(line, s) > 0.5 for s in scope_items):
            out_of_scope.append(line.strip())

    # Compute weighted completion %
    completion = round(
        100 * sum(1 for s in scored_items if s["match"]) / max(1, len(scored_items))
    )

    return {
        "completion": completion,
        "scored_items": scored_items,
        "matched": matched,
        "unmatched": unmatched,
        "out_of_scope": out_of_scope[:10],
        "change_order_suggestions": [
            f"Review {len(out_of_scope)} possible out‑of‑scope items."
        ] if out_of_scope else []
    }
