import os
import re
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz

# ========== Model Setup ==========
# Uses MiniLM for text; tries to load CLIP for image embeddings
try:
    clip_model = SentenceTransformer('clip-ViT-B-32')
    print("✅ CLIP model loaded for image intelligence.")
except Exception:
    clip_model = None
    print("⚠️ CLIP model not available, image AI disabled.")

text_model = SentenceTransformer('all-MiniLM-L6-v2')
SCOPE_DIR = "static/scope"
THRESHOLD = 0.65


# ========== Helper: Clean & Parse ==========
def clean_scope_text(text):
    text = re.sub(r"[^\x00-\x7F]+", "", text).strip()
    if len(text) < 5:
        return ""
    if text.lower().startswith(("client", "project", "date", "prepared by", "include", "scope", "description", "location")):
        return ""
    if any(bad in text.lower() for bad in ["no ", "not ", "excluded", "without", "does not", "will not"]):
        return ""
    return text


def parse_scope_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            import fitz
            doc = fitz.open(file_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        elif ext == ".docx":
            from docx import Document
            return "\n".join(p.text for p in Document(file_path).paragraphs)
        elif ext in [".xls", ".xlsx"]:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string(index=False)
        elif ext == ".txt":
            with open(file_path, encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"[Scope Parser] Error reading {file_path}: {e}")
    return ""


def load_scope_for_project(project_id):
    scope_path = os.path.join(SCOPE_DIR, f"scope_{project_id}.txt")
    if not os.path.exists(scope_path):
        return []
    with open(scope_path, encoding="utf-8") as f:
        lines = [clean_scope_text(line) for line in f]
    return [l for l in lines if l]


# ========== Helper: Image Embeddings ==========
def encode_images(image_paths):
    if not clip_model:
        return []
    vectors = []
    for path in image_paths:
        try:
            img = Image.open(path).convert("RGB").resize((224, 224))
            img_embed = clip_model.encode(img, convert_to_tensor=False, normalize_embeddings=True)
            vectors.append(img_embed)
        except Exception as e:
            print(f"[Image Encode] Skipped {path}: {e}")
    return vectors


# ========== Main Comparison ==========
def analyze_scope_vs_log(scope_items, log_texts, image_paths=None, threshold=THRESHOLD):
    if not scope_items:
        return {"completion": 0, "scored_items": [], "out_of_scope": ["⚠️ No scope items provided."]}

    # Combine all text inputs
    combined_log = " ".join(log_texts.values()).strip()
    if not combined_log:
        return {"completion": 0, "scored_items": [], "out_of_scope": ["⚠️ No daily log text available."]}

    # Encode log + scope embeddings
    log_embed = text_model.encode([combined_log])[0].reshape(1, -1)
    scope_embeds = text_model.encode(scope_items)

    # Encode images (if CLIP available)
    image_embeds = encode_images(image_paths or [])
    avg_img_embed = np.mean(image_embeds, axis=0).reshape(1, -1) if len(image_embeds) > 0 else None

    matched = 0
    scored_items = []

    for item, s_embed in zip(scope_items, scope_embeds):
        scope_vec = np.array(s_embed).reshape(1, -1)
        text_score = cosine_similarity(scope_vec, log_embed)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), combined_log.lower()) / 100
        img_score = cosine_similarity(scope_vec, avg_img_embed)[0][0] if avg_img_embed is not None else 0
        final_score = max(text_score, fuzzy_score, img_score)

        match = final_score >= threshold
        if match:
            matched += 1

        scored_items.append({
            "scope": item,
            "confidence": float(round(final_score * 100, 1)),  # ensure JSON-safe float
            "match": bool(match)  # ensure JSON-safe bool
        })

    percent = round((matched / len(scope_items)) * 100, 1)
    print(f"[AI Compare] ✅ {matched}/{len(scope_items)} matched → {percent}% complete")

    # Out-of-scope detection (simple keyword filter)
    out_of_scope = []
    known_ignore = ["ppe", "tailgate", "meeting", "safety"]
    log_lines = [l.strip() for l in combined_log.split("\n") if len(l.strip()) > 3]
    for line in log_lines:
        if any(kw in line.lower() for kw in known_ignore):
            continue
        if all(fuzz.partial_ratio(line.lower(), s.lower()) < 60 for s in scope_items):
            out_of_scope.append(line)

    return {
        "completion": float(percent),
        "scored_items": scored_items,
        "out_of_scope": out_of_scope[:10]
    }
