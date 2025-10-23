import os
import io
from PIL import Image, ImageOps

# ===============================
# Compression Configuration
# ===============================
MAX_FILE_SIZE_MB = 10                # target max file size per image
TARGET_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
INITIAL_QUALITY = 85
MIN_QUALITY = 30
MAX_DIMENSION = 1920                 # resize large images before saving

# ===============================
# Main Compression Function
# ===============================
def compress_and_rotate_image(input_path, output_path=None, target_size=TARGET_SIZE_BYTES):
    """
    Compress and auto‑rotate image based on EXIF.
    Ensures final file size < ~10 MB while maintaining reasonable quality.
    """

    try:
        img = Image.open(input_path)

        # Auto‑correct orientation via EXIF
        img = ImageOps.exif_transpose(img)

        # Resize down if too large
        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

        # Convert to JPEG for efficient compression
        img = img.convert("RGB")

        # Define output path
        if output_path is None:
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}_compressed.jpg"
        else:
            if not output_path.lower().endswith(".jpg"):
                output_path = os.path.splitext(output_path)[0] + "_compressed.jpg"

        # Iterative compression loop
        quality = INITIAL_QUALITY
        while quality >= MIN_QUALITY:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=quality)
            size = buffer.tell()

            if size <= target_size:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                print(f"[Image Compression] ✅ {os.path.basename(input_path)} → {round(size/1024/1024, 2)} MB @ Q={quality}")
                break
            quality -= 5

        # Save even if over target size
        if quality < MIN_QUALITY:
            with open(output_path, "wb") as f:
                f.write(buffer.getvalue())
            print(f"[Image Compression] ⚠️ {os.path.basename(input_path)} still >10 MB @ min Q={MIN_QUALITY}")

        return output_path

    except Exception as e:
        print(f"[Image Compression] ❌ Error processing {input_path}: {e}")
        return input_path


# ===============================
# Temp Cleanup Helper
# ===============================
def clean_temp_images(directory="static/uploads"):
    """
    Deletes leftover temporary _compressed files to save storage.
    Call after PDF generation or on a timed job.
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
        print(f"[Image Compression] 🧹 Cleaned {deleted} temp file(s).")
    else:
        print(f"[Image Compression] ℹ️ No temp files to clean.")
