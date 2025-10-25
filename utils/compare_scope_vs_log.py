import json
import difflib

def compare_scope_vs_log(scope_json_path, crew_notes, work_done, image_captions=[]):
    try:
        with open(scope_json_path, 'r') as f:
            scope_checklist = json.load(f)
    except Exception as e:
        return f"Error reading scope file: {e}"

    log_text = f"{crew_notes}\n{work_done}\n" + "\n".join(image_captions)
    log_text = log_text.lower()

    matched = []
    unmatched = []
    extra = []

    for item in scope_checklist:
        item_clean = item.lower()
        if item_clean in log_text or any(closer_match(item_clean, log_text)):
            matched.append(item)
        else:
            unmatched.append(item)

    # Optional: Detect extra (unusual) items from log
    # For now we’ll just detect phrases in logs not found in scope items
    all_scope_words = " ".join(scope_checklist).lower()
    if "concrete" in log_text and "concrete" not in all_scope_words:
        extra.append("Concrete slab work (not in scope)")

    # Completion %
    completion_pct = int((len(matched) / len(scope_checklist)) * 100) if scope_checklist else 0

    # Summary block for PDF Page 3
    summary = []
    for item in matched:
        summary.append(f"✅ {item}")
    for item in unmatched:
        summary.append(f"🔶 {item} – not yet reported in log")
    for item in extra:
        summary.append(f"🟦 {item} – extra work, consider flagging for change order")

    progress_bar = "█" * (completion_pct // 10) + "░" * (10 - (completion_pct // 10))
    summary.insert(0, f"📊 Estimated Completion: {completion_pct}%\n{progress_bar}")

    return "\n".join(summary)

def closer_match(phrase, text, cutoff=0.8):
    """Fuzzy match a phrase within the text using difflib"""
    matches = difflib.get_close_matches(phrase, text.split(), n=1, cutoff=cutoff)
    return matches
