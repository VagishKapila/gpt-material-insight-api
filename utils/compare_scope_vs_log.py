# compare_scope_vs_log.py
import re
from difflib import SequenceMatcher


def normalize(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower())


def fuzzy_match(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def compare_scope_vs_log(scope_items, work_done, threshold=0.45):
    matched = []
    missing = []
    out_of_scope = []

    for item in scope_items:
        if fuzzy_match(item, work_done) > threshold:
            matched.append(item)
        else:
            missing.append(item)

    work_items = [line.strip() for line in work_done.split("\n") if line.strip()]
    for line in work_items:
        if not any(fuzzy_match(line, scope_item) > threshold for scope_item in scope_items):
            out_of_scope.append(line)

    percent_complete = int((len(matched) / max(len(scope_items), 1)) * 100)

    return {
        "matched": matched,
        "missing": missing,
        "out_of_scope": out_of_scope,
        "percent_complete": percent_complete,
    }


def generate_scope_summary(data):
    scope_items = data.get("scope_items", [])
    work_done = data.get("work_done", "")

    if not scope_items:
        return "Scope file not uploaded or empty.", 0

    result = compare_scope_vs_log(scope_items, work_done)

    summary = ["AI / SCOPE ANALYSIS", ""]
    summary.append(f"Matched: {len(result['matched'])}")
    summary.append(f"Missing: {len(result['missing'])}")
    summary.append(f"Out of Scope: {len(result['out_of_scope'])}")
    summary.append(f"Completion: {result['percent_complete']}%")
    summary.append("")

    if result['matched']:
        summary.append("✔️ Matched:")
        for item in result['matched']:
            summary.append(f"- {item}")
        summary.append("")

    if result['missing']:
        summary.append("❗ Missing (Not Done Yet):")
        for item in result['missing']:
            summary.append(f"- {item}")
        summary.append("")

    if result['out_of_scope']:
        summary.append("⚠️ Out of Scope (Potential Change Order):")
        for item in result['out_of_scope']:
            summary.append(f"- {item}")

    return "\n".join(summary), result['percent_complete']
