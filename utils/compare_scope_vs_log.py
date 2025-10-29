import os
import re
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz

model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text):
    return re.sub(r"[^\x00-\x7F]+", "", text.strip())

def embed_texts(texts):
    return model.encode([clean_text(t) for t in texts], convert_to_numpy=True)

def analyze_scope_vs_log(scope_file_path, form_data, image_paths):
    try:
        with open(scope_file_path, "r", encoding="utf-8") as f:
            scope_lines = [clean_text(line) for line in f if len(line.strip()) > 4]
    except Exception as e:
        return {"error": f"Could not read scope file: {str(e)}"}

    combined_log = " ".join([
        form_data.get("work_done", ""),
        form_data.get("crew_notes", ""),
        form_data.get("safety_notes", "")
    ]).strip()

    log_embedding = embed_texts([combined_log])
    scope_embeddings = embed_texts(scope_lines)

    # Ensure log embedding is 2D
    if log_embedding.ndim == 1:
        log_embedding = log_embedding.reshape(1, -1)

    scored_items = []
    out_of_scope = []

    for i, line in enumerate(scope_lines):
        scope_embed = scope_embeddings[i].reshape(1, -1)
        try:
            cosine_score = float(cosine_similarity(scope_embed, log_embedding)[0][0])
        except Exception as e:
            cosine_score = 0.0

        fuzzy_score = fuzz.partial_ratio(line.lower(), combined_log.lower()) / 100.0
        hybrid_score = (cosine_score + fuzzy_score) / 2.0

        match = hybrid_score > 0.45
        scored_items.append({
            "scope": line,
            "confidence": int(round(hybrid_score * 100)),
            "match": match
        })

        if not match:
            out_of_scope.append(line)

    # Estimated completion only includes matched items
    matched = [item["confidence"] for item in scored_items if item["match"]]
    completion = round(sum(matched) / len(scope_lines), 1) if scope_lines else 0

    # ✅ Bonus Logging for Debugging
    print(f"\n--- Scope AI Debug ---")
    print(f"Total Scope Items: {len(scope_lines)}")
    print(f"Log text (first 120 chars): {combined_log[:120]}")
    print(f"Log embedding shape: {log_embedding.shape}")
    print(f"First scope line: {scope_lines[0] if scope_lines else 'None'}")
    print(f"First cosine similarity: {scored_items[0]['confidence'] if scored_items else 'N/A'}%")
    print(f"Estimated Completion: {completion}%")
    print(f"Out-of-scope count: {len(out_of_scope)}")
    print(f"----------------------\n")

    return {
        "completion": completion,
        "scored_items": scored_items,
        "out_of_scope": out_of_scope
    }
