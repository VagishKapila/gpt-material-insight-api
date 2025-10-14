
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return {'status': 'ok', 'message': 'Material Insight API is running'}

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    data = request.json
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({'error': 'image_url is required'}), 400

    # Simulate AI detection result from image
    detected_material = "sheetrock"

    # Simulate material price lookup
    result = {
        "material": detected_material,
        "cheapest_found": {
            "supplier": "Lowe's",
            "price": "$8.35/sheet",
            "location": "123 Main St, Sacramento, CA",
            "url": "https://lowes.com/sheetrock-deal"
        },
        "message": f"Cheaper {detected_material} available at Lowe’s for $8.35."
    }

    return jsonify(result)
