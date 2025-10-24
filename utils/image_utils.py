from PIL import Image, ImageFile, ExifTags
import os
import time

ImageFile.LOAD_TRUNCATED_IMAGES = True

def correct_image_orientation(image_path):
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            orientation = None
            for key, value in ExifTags.TAGS.items():
                if value == 'Orientation':
                    orientation = key
                    break

            if exif and orientation in exif:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
            return img.copy()
    except Exception as e:
        print(f"⚠️ EXIF rotation failed for {image_path}: {e}")
        return None

def preprocess_images(image_paths):
    processed_images = []

    for path in image_paths:
        print(f"\n📸 Processing: {path}")
        try:
            file_size = os.path.getsize(path)
            print(f"📏 Size: {file_size / 1024:.2f} KB")

            img = correct_image_orientation(path)
            if img is None:
                print("⚠️ Fallback: Open without EXIF rotation")
                img = Image.open(path)

            img_format = img.format or 'Unknown'
            print(f"📂 Format: {img_format}")

            safe_path = path.rsplit(".", 1)[0] + "_safe.png"
            img.save(safe_path, format="PNG")
            processed_images.append(safe_path)
            print(f"✅ Converted to: {safe_path}")

        except Exception as e:
            print(f"❌ Image processing failed for {path}: {e}")

        time.sleep(1)

    return processed_images
