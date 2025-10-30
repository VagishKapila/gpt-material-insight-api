# utils/compare_scope_vs_log.py
import os
import numpy as np
from sentence_transformers import SentenceTransformer, util
from utils.scope_parser import parse_scope_file
from PIL import Image
import torch
import clip

# Load models once
clip_model, clip_preprocess = clip.load("ViT-B/32", device="cpu")
text_model = SentenceTransformer('all-MiniLM-L6-v2')

def clip_score(text, image_path):
    try:
        image = clip_preprocess(Image.open(image_path)).unsqueeze(0).to("cpu")
        text_tokens = clip.tokenize([text]).to("cpu")
        with torch.no_grad():
            image_features = clip_model.encode_image(image)
            text_features = clip_model.encode_text(text_tokens)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = (image_features @ text_features.T).item()
        return similarity * 100
    except Exception:
        return 0.0

def analyze_scope_vs_log(scope_path, form_data, image_paths):
    # 🔍 Step 1: Parse scope file
    scope_items = parse_scope_file(scope_path)
    if not scope_items:
        return {"completion": 0, "scored_items": [], "out_of_scope": []}

    # 🔍 Step 2: Merge form data
    combined_text = " ".join([
        form_data.get("work_done", ""),
        form_data.get("crew_notes", ""),
        form_data.get("safety_notes", "")
    ])

    scored_items = []
    matched_count = 0

    # 🔍 Step 3: Embedding
    scope_embeddings = text_model.encode(scope_items, convert_to_tensor=True)
    text_embedding = text_model.encode(combined_text, convert_to_tensor=True)

    for idx, scope in enumerate(scope_items):
        text_score = util.cos_sim(scope_embeddings[idx], text_embedding).item() * 100
        best_image = None
        best_clip_score = 0

        for img_path in image_paths:
            score = clip_score(scope, img_path)
            if score > best_clip_score:
                best_clip_score = score
                best_image = img_path

        final_score = (0.6 * text_score) + (0.4 * best_clip_score)
        is_match = final_score > 50

        if is_match:
            matched_count += 1

        scored_items.append({
            "scope": scope,
            "match": is_match,
            "confidence": round(final_score),
            "matched_image": best_image if is_match else None
        })

    # 🔍 Step 4: Summary
    completion = round((matched_count / len(scope_items)) * 100, 1)
    return {
        "completion": completion,
        "scored_items": scored_items,
        "out_of_scope": []
    }
