import os
import re
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from fuzzywuzzy import fuzz

model = SentenceTransformer('all-MiniLM-L6-v2')
SCOPE_DIR = "static/scope"
IMAGE_EMBEDDING_DIM = 384

def clean_scope_text(text):
    text = re.sub(r"[^\x00-\x7F]+", "", text).strip()
    if len(text) < 5 or text.lower().startswith(("client", "project", "date")):
        return ""
    if any(bad in text.lower() for bad in ["no ", "not ", "excluded", "without"]):
        return ""
    return text

def parse_scope_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        import fitz
        return "\n".join(p.get_text() for p in fitz.open(file_path))
    elif ext == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(file_path).paragraphs)
    elif ext in [".xls", ".xlsx"]:
        import pandas as pd
        df = pd.read_excel(file_path)
        return df.to_string(index=False)
    elif ext == ".txt":
        return open(file_path).read()
    return ""

def load_scope_for_project(project_id):
    path = os.path.join(SCOPE_DIR, f"scope_{project_id}.txt")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [clean_scope_text(l) for l in f if clean_scope_text(l)]

def encode_images(image_paths):
    vectors = []
    for path in image_paths:
        try:
            img = Image.open(path).convert("RGB").resize((224, 224))
            img_embedding = model.encode(img, convert_to_tensor=False)
            vectors.append(img_embedding)
        except Exception:
            pass
    return vectors

def analyze_scope_vs_log(scope_items, log_texts, image_paths=None, threshold=0.65):
    if not scope_items:
        return {"completion": 0, "scored_items": [], "out_of_scope": ["⚠️ No scope provided."]}

    combined_log = " ".join(log_texts.values()).strip()
    log_embed = model.encode([combined_log])[0].reshape(1, -1)
    scope_embeds = model.encode(scope_items)

    image_embeds = encode_images(image_paths or [])
    avg_img_embed = np.mean(image_embeds, axis=0).reshape(1, -1) if image_embeds else None

    matched = 0
    scored = []

    for item, scope_embed in zip(scope_items, scope_embeds):
        scope_vec = np.array(scope_embed).reshape(1, -1)
        text_score = cosine_similarity(scope_vec, log_embed)[0][0]
        fuzzy_score = fuzz.partial_ratio(item.lower(), combined_log.lower()) / 100

        img_score = cosine_similarity(scope_vec, avg_img_embed)[0][0] if avg_img_embed is not None else 0
        final_score = max(text_score, fuzzy_score, img_score)
        match = final_score >= threshold
        if match:
            matched += 1
        scored.append({
            "scope": item,
            "confidence": round(final_score * 100, 1),
            "match": match
        })

    percent = round((matched / len(scope_items)) * 100, 1)
    return {"completion": percent, "scored_items": scored, "out_of_scope": []}
