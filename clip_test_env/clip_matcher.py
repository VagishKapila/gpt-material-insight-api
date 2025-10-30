import torch
import clip
from PIL import Image
import os
import traceback

# --- Load CLIP model once at import ---
print("🧠 Loading CLIP model ...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
print("✅ CLIP model ready on", device)

# --- Function: run CLIP-based matching ---
def run_clip_match_test(scope_file_path, image_paths):
    try:
        # --- Load scope lines ---
        with open(scope_file_path, "r", encoding="utf-8") as f:
            scope_lines = [line.strip() for line in f if len(line.strip()) > 4]

        if not scope_lines:
            return {"error": "Scope file is empty or unreadable"}

        # --- Encode scope text ---
        text_tokens = clip.tokenize(scope_lines).to(device)
        with torch.no_grad():
            text_features = model.encode_text(text_tokens).float()

        # --- Encode images ---
        image_features_list = []
        for path in image_paths:
            try:
                image = preprocess(Image.open(path)).unsqueeze(0).to(device)
                with torch.no_grad():
                    image_features = model.encode_image(image).float()
                image_features_list.append(image_features)
            except Exception as e:
                print(f"⚠️ Failed to process image {path}: {e}")

        if not image_features_list:
            return {"error": "No valid images processed"}

        # --- Compare each scope line with each image ---
        results = []
        for i, text_feat in enumerate(text_features):
            text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
            match_scores = []
            for j, img_feat in enumerate(image_features_list):
                img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
                score = (text_feat @ img_feat.T).item()
                match_scores.append(score)
            best_score = max(match_scores)
            best_idx = match_scores.index(best_score)
            results.append({
                "scope_line": scope_lines[i],
                "best_image": os.path.basename(image_paths[best_idx]),
                "score": round(best_score * 100, 2)
            })

        print(f"✅ CLIP processed {len(scope_lines)} scope items vs {len(image_paths)} images")
        return {"matches": results}

    except Exception as e:
        print("❌ [CLIP ERROR]", e)
        traceback.print_exc()
        return {"error": str(e), "traceback": traceback.format_exc()}
