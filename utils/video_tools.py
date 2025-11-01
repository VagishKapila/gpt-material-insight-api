# utils/video_tools.py

import os
import subprocess

def generate_video_thumbnail(video_path):
    """
    Generate a thumbnail JPG from a video file using FFmpeg.
    Returns the path to the thumbnail, or None if failed.
    """
    try:
        thumb_path = video_path.rsplit(".", 1)[0] + "_thumb.jpg"
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-ss", "00:00:01.000", "-vframes", "1", thumb_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(thumb_path):
            print(f"🎞️ Thumbnail generated: {thumb_path}")
            return thumb_path
        else:
            print(f"⚠️ Thumbnail not found after FFmpeg run.")
            return None
    except Exception as e:
        print(f"❌ FFmpeg thumbnail generation failed: {e}")
        return None
