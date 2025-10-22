# utils/ai_analysis.py

from .image_analyzer import classify_image

def analyze_images_with_mobilenet(photo_paths):
    results = []
    for path in photo_paths:
        try:
            label, confidence = classify_image(path)
            results.append({
                "image_path": path,
                "label": label,
                "confidence": confidence
            })
        except Exception as e:
            results.append({
                "image_path": path,
                "label": "Error",
                "confidence": 0.0,
                "error": str(e)
            })
    return results
