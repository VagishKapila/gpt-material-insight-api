# utils/pdf_generator.py (Video thumbnail + fallback link)

import cv2
import os

def generate_video_thumbnail(video_path, output_dir="static/uploads"):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return None

        # Read first frame
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Could not read frame from: {video_path}")
            return None

        thumbnail_path = os.path.join(
            output_dir,
            os.path.basename(video_path).rsplit(".", 1)[0] + "_thumb.jpg"
        )
        cv2.imwrite(thumbnail_path, frame)
        print(f"🎞️ Generated thumbnail for {video_path}")
        return thumbnail_path
    except Exception as e:
        print(f"❌ Thumbnail generation error: {e}")
        return None
