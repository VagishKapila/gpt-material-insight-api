import torch
import clip
from PIL import Image
import os

# Load CLIP model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Load test image
image_path = "test_image.jpg"
image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)

# Load scope lines
with open("test_scope.txt", "r") as f:
    scope_lines = [line.strip() for line in f if len(line.strip()) > 0]

# Encode scope lines
text_tokens = clip.tokenize(scope_lines).to(device)
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text_tokens)

    # Normalize
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    # Compute similarity
    similarity = (100.0 * image_features @ text_features.T).squeeze().tolist()

# Print results
print("\n🔍 Top CLIP Matches:\n")
ranked = sorted(zip(similarity, scope_lines), reverse=True)
for score, line in ranked:
    print(f"{score:.2f}%  -  {line}")
