from PIL import Image, ExifTags

def fix_image_orientation(image_path, max_size=(1200, 1200)):
    try:
        image = Image.open(image_path)

        # Correct orientation if EXIF exists
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

        # Resize image while keeping aspect ratio
        image.thumbnail(max_size, Image.LANCZOS)

        # Save (overwrite original)
        image.save(image_path, optimize=True, quality=85)
    except Exception:
        pass  # Ignore failures silently
