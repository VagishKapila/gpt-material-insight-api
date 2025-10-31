# utils/compare_scope_vs_log.py (CLIP REMOVED, STABLE)

import os
import traceback
from sentence_transformers import SentenceTransformer, util

text_model = SentenceTransformer("all-MiniLM-L6-v2")

def analyze_scope_vs_log(scope_path, form_data, image_paths):
    try:
        with open(scope_path, "r", encoding="utf-8") as f:
            scope_lines = [line.strip() for line in f if len(line.strip()) > 4]

        all_log_text = "\n".join([
            form_data.get("work_done", ""),
            form_data.get("crew_notes", ""),
            form_data.get("safety_notes", "")
        ]).lower()

        log_embedding = text_model.encode(all_log_text, convert_to_tensor=True)

        scored_items = []
        out_of_scope = []

        for line in scope_lines:
            text_embed = text_model.encode(line, convert_to_tensor=True)
            text_score = float(util.cos_sim(text_embed, log_embedding)[0][0]) * 100
            match = text_score >= 25

            scored_items.append({
                "scope": line,
                "confidence": round(text_score, 1),
                "match": match,
                "matched_image": None  # CLIP removed = no image matching
            })

            if not match:
                out_of_scope.append(line)

        estimated_completion = sum(i["confidence"] for i in scored_items if i["match"]) / max(len(scored_items), 1)

        return {
            "completion": round(estimated_completion, 1),
            "scored_items": scored_items,
            "out_of_scope": out_of_scope
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "completion": 0,
            "scored_items": [],
            "out_of_scope": [],
            "error": str(e)
        }
