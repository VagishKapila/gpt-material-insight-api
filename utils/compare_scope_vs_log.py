from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz

def analyze_scope_vs_log(scope_items, work_done, crew_notes, safety_notes):
    if not scope_items:
        return {
            "completion": 0,
            "scored_items": [],
            "out_of_scope": ["⚠️ No scope items loaded for project."]
        }

    full_log = f"{work_done}\n{crew_notes}\n{safety_notes}".strip()
    if not full_log:
        return {
            "completion": 0,
            "scored_items": [],
            "out_of_scope": ["⚠️ No log data provided."]
        }

    vectorizer = TfidfVectorizer().fit(scope_items + [full_log])
    log_vec = vectorizer.transform([full_log])

    matched = []
    unmatched = []
    scored_items = []

    for item in scope_items:
        scope_vec = vectorizer.transform([item])
        tfidf_score = cosine_similarity(scope_vec, log_vec)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), full_log.lower()) / 100

        final_score = max(tfidf_score, fuzzy_score)

        match = final_score >= 0.65
        scored_items.append({
            "scope": item,
            "confidence": round(final_score, 2),
            "match": match
        })

        if match:
            matched.append(item)
        else:
            unmatched.append(item)

    # Out-of-scope detection (basic line scan)
    log_lines = [line.strip() for line in full_log.split('\n') if line.strip()]
    out_of_scope = []
    for line in log_lines:
        if all(fuzz.partial_ratio(line.lower(), item.lower()) < 60 for item in scope_items):
            out_of_scope.append(line)

    percent_complete = int((len(matched) / len(scope_items)) * 100)

    return {
        "completion": percent_complete,
        "scored_items": scored_items,
        "out_of_scope": out_of_scope[:10]  # limit output
    }
