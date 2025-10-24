from PIL import Image, ImageOps
import os

def preprocess_images(image_paths):
    processed_paths = []
    for idx, img_path in enumerate(image_paths):
        try:
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img)  # ⬅ Rotate based on EXIF data
            safe_path = f"processed_{idx}.jpg"
            img.save(safe_path)
            processed_paths.append(safe_path)
        except Exception as e:
            print(f"[❌ Error] Preprocessing image {img_path}: {e}")
    return processed_paths
