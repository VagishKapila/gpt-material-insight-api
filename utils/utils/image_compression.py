import os
from PIL import Image, ExifTags
import io

MAX_FILE_SIZE_MB = 10
TARGET_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
INITIAL_QUALITY = 85
MIN_QUALITY = 30

def rotate_image_if_needed(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(orientation)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except Exception as e:
        print(f"[Image Compression] Warning: Cannot auto-rotate image. {str(e)}")
    return image

def compress_and_rotate_image(input_path, output_path=None, target_size=TARGET_SIZE_BYTES):
    try:
        img = Image.open(input_path)
        img = rotate_image_if_needed(img)

        quality = INITIAL_QUALITY
        img_format = img.format if img.format else "JPEG"

        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_compressed{ext}"

        while quality >= MIN_QUALITY:
            buffer = io.BytesIO()
            img.save(buffer, format=img_format, optimize=True, quality=quality)
            size = buffer.tell()

            if size <= target_size:
                with open(output_path, "wb") as f:
                    f.write(buffer.getvalue())
                print(f"[Image Compression] ✅ {os.path.basename(input_path)} → {round(size/1024/1024, 2)} MB @ Quality {quality}")
                return output_path
            quality -= 5

        # Save the best we could
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())
        print(f"[Image Compression] ⚠️ Saved {os.path.basename(input_path)} > 10MB @ Quality {quality + 5}")
        return output_path

    except Exception as e:
        print(f"[Image Compression] ❌ Error compressing {input_path}: {str(e)}")
        return input_path
