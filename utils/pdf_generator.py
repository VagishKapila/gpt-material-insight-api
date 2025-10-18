from PIL import Image, ImageDraw, ImageFont
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import os

# Load BLIP captioning model once at the top level
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

def analyze_and_overlay(image_path, output_path):
    """
    Automatically analyzes the input image, draws bounding boxes, and overlays AI-generated captions.
    Saves annotated image to output_path.
    """
    image = Image.open(image_path).convert("RGB")

    # Step 1: AI-generated Caption using BLIP
    inputs = processor(images=image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    # Step 2: Draw a simulated bounding box and overlay caption
    draw = ImageDraw.Draw(image)
    width, height = image.size
    box_width, box_height = width // 2, height // 3
    left = (width - box_width) // 2
    top = (height - box_height) // 2
    right = left + box_width
    bottom = top + box_height

    draw.rectangle([left, top, right, bottom], outline="red", width=4)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    # Add caption just above box
    text_position = (left, max(top - 30, 10))
    draw.text(text_position, caption, fill="red", font=font)

    image.save(output_path)
    return output_path, caption
