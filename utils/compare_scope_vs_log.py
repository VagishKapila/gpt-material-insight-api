import os
import re
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz
from transformers import CLIPProcessor, CLIPModel

# --- Initialize CLIP model (text + image unified embeddings, 512‑dim) ---
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

SCOPE_DIR = "static/scope"
EXCLUDE_WORDS = [
    "no ", "not ", "exclude", "without", "doesn't", "isn't", "cannot", "never"
]


# -------------------------------------------------------------
# 🔹  Helper: clean up scope lines
# -------------------------------------------------------------
def clean_scope_text(text):
    text = re.sub(r"[^\x00-\x7F]+", "", text).strip()
    if len(text) < 5:
        return ""
    if text.lower().startswith(("client", "project", "date", "prepared by")):
        return ""
    if any(word in text.lower() for word in EXCLUDE_WORDS):
        return ""
    return text


# -------------------------------------------------------------
# 🔹  Parse uploaded scope files (PDF, DOCX, XLSX, TXT)
# -------------------------------------------------------------
def parse_scope_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        import fitz
        with fitz.open(file_path) as doc:
            text = "\n".join([p.get_text("text") for p in doc])
        return text
    elif ext == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(file_path).paragraphs)
    elif ext in [".xls", ".xlsx"]:
        import pandas as pd
        df = pd.read_excel(file_path)
        return df.to_string(index=False)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# -------------------------------------------------------------
# 🔹  Load project scope text
# -------------------------------------------------------------
def load_scope_for_project(project_id):
    path = os.path.join(SCOPE_DIR, f"scope_{project_id}.txt")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        lines = [clean_scope_text(l) for l in f]
    return [l for l in lines if l]


# -------------------------------------------------------------
# 🔹  Encode text & images with CLIP
# -------------------------------------------------------------
def encode_text_clip(texts):
    if not texts:
        return np.zeros((1, 512))
    inputs = clip_processor(text=texts, return_tensors="pt", padding=True, truncation=True)
    with np.errstate(all="ignore"):
        features = clip_model.get_text_features(**inputs).detach().numpy()
    return features


def encode_image_clip(paths):
    embeds = []
    for p in paths or []:
        try:
            img = Image.open(p).convert("RGB")
            inputs = clip_processor(images=img, return_tensors="pt")
            feat = clip_model.get_image_features(**inputs).detach().numpy()
            embeds.append(feat[0])
        except Exception:
            continue
    if not embeds:
        return None
    return np.mean(np.stack(embeds), axis=0).reshape(1, -1)


# -------------------------------------------------------------
# 🔹  Main analysis (hybrid text + image)
# -------------------------------------------------------------
def analyze_scope_vs_log(scope_items, log_texts, image_paths=None, threshold=0.65):
    """
    Compare scope items vs combined daily log (text + optional photo embeddings)
    """
    if not scope_items:
        return {"completion": 0, "scored_items": [], "out_of_scope": ["⚠️ No scope items."]}

    # Combine textual inputs
    combined_log = " ".join(log_texts.values()).strip()
    text_embed = encode_text_clip([combined_log])[0].reshape(1, -1)

    # Encode all scope items
    scope_embeds = encode_text_clip(scope_items)

    # Encode images (average embedding)
    img_embed = encode_image_clip(image_paths)
    use_image = img_embed is not None

    matched = 0
    results = []

    for item, scope_vec in zip(scope_items, scope_embeds):
        scope_vec_2d = scope_vec.reshape(1, -1)

        # --- text similarity ---
        text_score = cosine_similarity(scope_vec_2d, text_embed)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), combined_log.lower()) / 100

        # --- image similarity (optional) ---
        img_score = cosine_similarity(scope_vec_2d, img_embed)[0][0] if use_image else 0

        # --- hybrid weighting (70% text/fuzzy + 30% image) ---
        hybrid_score = (0.7 * max(text_score, fuzzy_score)) + (0.3 * img_score)
        match = hybrid_score >= threshold

        if match:
            matched += 1

        results.append({
            "scope": item,
            "confidence": round(hybrid_score * 100, 1),
            "match": match
        })

    completion = round((matched / len(scope_items)) * 100, 1)
    return {
        "completion": completion,
        "scored_items": results,
        "out_of_scope": []
    }
