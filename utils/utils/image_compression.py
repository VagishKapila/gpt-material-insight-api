from PIL import Image, ExifTags
import os

def auto_rotate_image(img):
    try:
        exif = img._getexif()
        if exif is not None:
            orientation_key = next(
                key for key, val in ExifTags.TAGS.items() if val == 'Orientation'
            )
            orientation = exif.get(orientation_key, None)
            if orientation == 3:
                return img.rotate(180, expand=True)
            elif orientation == 6:
                return img.rotate(270, expand=True)
            elif orientation == 8:
                return img.rotate(90, expand=True)
    except Exception:
        pass
    return img

def compress_and_rotate_image(image_path, output_path, max_width=1024, quality=75):
    with Image.open(image_path) as img:
        img = auto_rotate_image(img)

        if img.width > max_width:
            ratio = max_width / float(img.width)
            height = int(float(img.height) * ratio)
            img = img.resize((max_width, height), Image.LANCZOS)

        img.save(output_path, optimize=True, quality=quality)
