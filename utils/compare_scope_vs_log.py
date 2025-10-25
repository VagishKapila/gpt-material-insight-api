# compare_scope_vs_log.py

import os
import json
from difflib import SequenceMatcher
from typing import List, Dict, Tuple

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
    # For now, split by lines and keep non-empty meaningful lines
    lines = [line.strip() for line in raw_text.split("\n") if len(line.strip()) > 15]
    return lines

# ---------- MAIN COMPARISON ----------
def match_scope_vs_log(scope_items: List[str], daily_work: str) -> Dict:
    vectorizer = TfidfVectorizer().fit(scope_items + [daily_work])
    scope_vecs = vectorizer.transform(scope_items)
    log_vec = vectorizer.transform([daily_work])

    matched = []
    pending = []
    out_of_scope = []

    for i, scope in enumerate(scope_items):
        score = cosine_similarity(scope_vecs[i], log_vec)[0][0]
        if score >= SIMILARITY_THRESHOLD:
            matched.append(scope)
        else:
            pending.append(scope)

    # Naive logic for out-of-scope:
    extra_items = []
    for word in daily_work.split("\n"):
        if not any(similar(word, s) > 0.5 for s in scope_items):
            extra_items.append(word.strip())

    progress = round(100 * len(matched) / max(1, len(scope_items)))

    return {
        "progress": progress,
        "matched_items": matched,
        "pending_items": pending,
        "extra_items": extra_items[:10],
    }

# ---------- USAGE EXAMPLE ----------
if __name__ == "__main__":
    # For testing
    from pathlib import Path

    raw_scope_text = Path("/mnt/data/Demo, Grade, Trench 98 Upperoaks San Rafael1A.txt").read_text()
    scope_items = extract_scope_items(raw_scope_text)
    save_scope_for_project("project_1", scope_items)

    fake_log = """
    Dug trench 2ft wide
    Installed 1 inch gas line
    Rebar placed at 12in spacing
    Safety cones placed near entry
    """
    result = match_scope_vs_log(scope_items, fake_log)
    print(json.dumps(result, indent=2))
