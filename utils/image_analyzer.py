# utils/image_analyzer.py

import torch
from torchvision import models, transforms
from PIL import Image
import os

# Load the ImageNet labels
with open(os.path.join(os.path.dirname(__file__), "imagenet_classes.txt")) as f:
    classes = [line.strip() for line in f.readlines()]

# Load the pre-trained model once
model = models.mobilenet_v2(pretrained=True)
model.eval()

# Define transform
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def classify_image(image_path):
    image = Image.open(image_path).convert("RGB")
    input_tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        output = model(input_tensor)
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_class = probabilities.argmax().item()
        label = classes[top_class]
        confidence = float(probabilities[top_class])
    
    return label, confidence
