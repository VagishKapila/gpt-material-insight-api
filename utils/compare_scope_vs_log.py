import os
import json
import re
from difflib import SequenceMatcher

SCOPE_DATA_DIR = os.path.join(os.path.dirname(__file__), "scope_data")


def load_scope(project_id="test_scope"):
    """Load the parsed scope checklist for a given project."""
    path = os.path.join(SCOPE_DATA_DIR, f"{project_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scope file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def compare_scope_vs_log(scope_checklist, log_text, log_photos=[]):
    matched = []
    flagged_missing = []
    out_of_scope = []

    # Normalize both scope items and log text
    log_text_combined = log_text.lower()
    log_text_combined += "\n" + "\n".join(log_photos)  # Include photo captions if any

    for item in scope_checklist:
        item_lower = item.lower()
        if item_lower in log_text_combined:
            matched.append(item)
        else:
            # Check for approximate match
            found_similar = False
            for sentence in log_text_combined.split("\n"):
                if similar(item_lower, sentence) > 0.75:
                    matched.append(item)
                    found_similar = True
                    break
            if not found_similar:
                flagged_missing.append(item)

    # Find out-of-scope statements
    known_scope_phrases = [item.lower() for item in scope_checklist]
    for sentence in log_text_combined.split("\n"):
        if not any(phrase in sentence for phrase in known_scope_phrases):
            if len(sentence.strip()) > 10:
                out_of_scope.append(sentence.strip())

    # Clean out-of-scope (remove obvious duplicates)
    out_of_scope = list(set(out_of_scope))

    # Calculate percent complete
    total = len(scope_checklist)
    complete = len(matched)
    percent = int((complete / total) * 100) if total > 0 else 0

    return {
        "matched": matched,
        "flagged_missing": flagged_missing,
        "out_of_scope": out_of_scope,
        "percent_complete": percent
    }


def save_comparison_result(result_dict, output_path):
    """Save results as both JSON and Markdown for debugging and PDF rendering."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save JSON
    json_path = output_path + ".json"
    with open(json_path, "w") as f:
        json.dump(result_dict, f, indent=2)

    # Save Markdown
    md_path = output_path + ".md"
    with open(md_path, "w") as f:
        f.write("### Scope Comparison Report\n\n")
        f.write(f"**Percent Complete:** {result_dict['percent_complete']}%\n\n")

        f.write("#### ✅ Matched Items\n")
        for item in result_dict["matched"]:
            f.write(f"- ✅ {item}\n")

        f.write("\n#### ⚠️ Missing Items\n")
        for item in result_dict["flagged_missing"]:
            f.write(f"- ⚠️ {item}\n")

        f.write("\n#### 🚫 Out-of-Scope Mentions\n")
        for line in result_dict["out_of_scope"]:
            f.write(f"- 🚫 {line}\n")

    return json_path, md_path


# Optional test mode if you run this file directly
if __name__ == '__main__':
    try:
        scope = load_scope("test_scope")
        mock_log = """
        Trench from front downspout to back fence complete.
        Trench from side of house to tree area in progress.
        Compact trench areas complete.
        Concrete pad poured (not in scope)
        Remove gravel finished.
        """
        result = compare_scope_vs_log(scope, mock_log)
        json_file, md_file = save_comparison_result(result, "debug_output/test_compare")
        print(f"Test passed. Output saved to: {json_file}, {md_file}")
    except Exception as e:
        print(f"❌ Error during test run: {e}")
