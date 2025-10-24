from PIL import Image, ExifTags

def preprocess_images(image_paths):
    processed_paths = []
    for path in image_paths:
        try:
            image = Image.open(path)
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == "Orientation":
                    break

            exif = image._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    image = image.rotate(180, expand=True)
                elif orientation_value == 6:
                    image = image.rotate(270, expand=True)
                elif orientation_value == 8:
                    image = image.rotate(90, expand=True)

            image.save(path)
        except Exception as e:
            print(f"Failed to process {path}: {e}")

        processed_paths.append(path)
    return processed_paths
