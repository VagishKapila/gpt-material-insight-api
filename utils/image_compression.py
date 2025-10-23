import os
import io
from PIL import Image, ImageOps

# ===============================
# Compression Configuration
# ===============================
MAX_FILE_SIZE_MB = 10
TARGET_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
INITIAL_QUALITY = 85
MIN_QUALITY = 30

def compress_and_rotate_image(input_path, output_path=None, target_size=TARGET_SIZE_BYTES):
    """
    Compresses and auto-rotates an image based on EXIF data.
    Ensures final file size is under ~10MB while maintaining visual quality.
    """

    try:
        # Open image
        img = Image.open(input_path)

        # Auto-rotate using EXIF (replaces manual rotation logic)
        img = ImageOps.exif_transpose(img)

        # Convert all formats to JPEG for efficient compression
        img = img.convert("RGB")

        # Define output path
        if output_path is None:
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}_compressed.jpg"
        else:
            if not output_path.lower().endswith(".jpg"):
                output_path = os.path.splitext(output_path)[0] + "_compressed.jpg"

        # Iteratively compress until under target size or quality floor reached
        quality = INITIAL_QUALITY
        while quality >= MIN_QUALITY:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=quality)
            size = buffer.tell()

            if size <= target_size:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                print(f"[Image Compression] ✅ {os.path.basename(input_path)} → {round(size/1024/1024, 2)} MB @ Quality {quality}")
                break
            quality -= 5

        # If no acceptable size found, save last version anyway
        if quality < MIN_QUALITY:
            with open(output_path, "wb") as f:
                f.write(buffer.getvalue())
            print(f"[Image Compression] ⚠️ {os.path.basename(input_path)} saved >10MB @ min quality {MIN_QUALITY}")

        return output_path

    except Exception as e:
        print(f"[Image Compression] ❌ Error compressing {input_path}: {str(e)}")
        return input_path


def clean_temp_images(directory="static/uploads"):
    """
    Deletes leftover temporary _compressed files to save storage.
    Use at the end of PDF generation or on a schedule.
    """
    deleted = 0
    for filename in os.listdir(directory):
        if filename.endswith("_compressed.jpg"):
            try:
                os.remove(os.path.join(directory, filename))
                deleted += 1
            except Exception as e:
                print(f"[Image Compression] ⚠️ Could not delete {filename}: {e}")
    if deleted > 0:
        print(f"[Image Compression] 🧹 Cleaned up {deleted} compressed temp file(s).")
