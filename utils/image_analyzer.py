import replicate
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

def analyze_and_overlay(image_url):
    # Load your Replicate API token from the environment
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise ValueError("REPLICATE_API_TOKEN is not set in the environment")

    # Initialize Replicate client
    replicate_client = replicate.Client(api_token=replicate_token)

    # Download the image from URL
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGB")

    # Run image captioning
    output = replicate_client.run(
        "salesforce/blip-2:ca061f69b8f1625c6cc56b72e3b3e5cc662fcd38c3f8659c129b3f6ea4f1a9f3",
        input={"image": image_url}
    )
    caption = output if isinstance(output, str) else output[0]

    # Draw caption on the image
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle([(0, 0), (image.width, 30)], fill="black")
    draw.text((10, 5), caption, font=font, fill="white")

    # Save locally for later use
    output_path = os.path.join("static", "captioned.jpg")
    os.makedirs("static", exist_ok=True)
    image.save(output_path)

    return caption, output_path
