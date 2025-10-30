# utils/compare_scope_vs_log.py

import os
import traceback
import torch
import clip
from PIL import Image
from sentence_transformers import SentenceTransformer, util

device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)
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

        scored_items = []
        out_of_scope = []

        log_embedding = text_model.encode(all_log_text, convert_to_tensor=True)

        # Prepare image features
        image_features = {}
        for img_path in image_paths:
            try:
                image = clip_preprocess(Image.open(img_path)).unsqueeze(0).to(device)
                with torch.no_grad():
                    features = clip_model.encode_image(image).float()
                image_features[img_path] = features
            except Exception as e:
                print(f"⚠️ Image load failed for {img_path}: {e}")
                continue

        for line in scope_lines:
            text_embed = text_model.encode(line, convert_to_tensor=True)
            text_score = float(util.cos_sim(text_embed, log_embedding)[0][0]) * 100

            tokens = clip.tokenize([line]).to(device)
            with torch.no_grad():
                text_clip_feat = clip_model.encode_text(tokens)[0]
                text_clip_feat /= text_clip_feat.norm()

            best_score = 0
            best_image = None

            for img_path, img_feat in image_features.items():
                img_feat = img_feat[0] / img_feat[0].norm()
                score = float((text_clip_feat @ img_feat.T).item()) * 100
                if score > best_score:
                    best_score = score
                    best_image = os.path.basename(img_path)

            final_score = round((text_score + best_score) / 2, 1) if best_image else round(text_score, 1)

            match = final_score >= 25
            scored_items.append({
                "scope": line,
                "confidence": final_score,
                "match": match,
                "matched_image": best_image or None
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
