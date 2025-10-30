
import torch
import clip
from PIL import Image
import os

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def run_clip_match_test(scope_path, image_paths):
    try:
        # Read scope items from the file
        with open(scope_path, 'r') as f:
            scope_items = [line.strip() for line in f if line.strip()]
    except Exception as e:
        return {"error": f"Failed to read scope file: {e}"}

    results = []

    for scope_item in scope_items:
        try:
            scope_tokens = clip.tokenize([scope_item]).to(device)
        except Exception as e:
            results.append({
                "scope_item": scope_item,
                "error": f"Tokenization error: {e}"
            })
            continue

        best_score = 0
        best_image = None

        for image_path in image_paths:
            try:
                image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)

                with torch.no_grad():
                    image_features = model.encode_image(image)
                    text_features = model.encode_text(scope_tokens)
                    similarity = (image_features @ text_features.T).item()

                    if similarity > best_score:
                        best_score = similarity
                        best_image = os.path.basename(image_path)

            except Exception as e:
                print(f"⚠️ Error processing {image_path}: {e}")
                continue

        results.append({
            "scope_item": scope_item,
            "best_image_match": best_image,
            "similarity_score": round(best_score, 4)
        })

    return results
