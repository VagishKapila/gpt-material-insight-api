import json
import os
import difflib
from datetime import datetime

def compare_scope_with_log(scope_json_path, daily_log_text, debug_save=True):
    try:
        with open(scope_json_path, 'r') as f:
            scope_items = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load scope: {e}"}

    matched = []
    flagged_missing = []
    out_of_scope = []

    log_lines = [line.strip().lower() for line in daily_log_text.splitlines() if line.strip()]

    for item in scope_items:
        item_lower = item.lower()
        match_found = any(
            difflib.SequenceMatcher(None, item_lower, line).ratio() > 0.75 for line in log_lines
        )
        if match_found:
            matched.append(item)
        else:
            flagged_missing.append(item)

    for line in log_lines:
        if not any(item.lower() in line for item in scope_items):
            out_of_scope.append(line)

    percent_complete = round((len(matched) / len(scope_items)) * 100) if scope_items else 0

    result = {
        "matched": matched,
        "flagged_missing": flagged_missing,
        "out_of_scope": out_of_scope,
        "percent_complete": percent_complete
    }

    if debug_save:
        os.makedirs("debug_output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_path = os.path.join("debug_output", f"compare_{timestamp}.json")
        with open(debug_path, 'w') as f:
            json.dump(result, f, indent=2)

    return result

# Example test run (remove or comment out in production)
if __name__ == "__main__":
    test_scope_path = "utils/scope_data/test_scope.json"
    test_log_path = "utils/scope_data/test_log.txt"
    try:
        with open(test_log_path, 'r') as f:
            test_log_text = f.read()
        output = compare_scope_with_log(test_scope_path, test_log_text)
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Test run failed: {e}")
