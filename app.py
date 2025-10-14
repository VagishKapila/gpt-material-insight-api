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

    # Simulated detection
    detected_material = "sheetrock"

    # Simulated result
    result = {
        "material": detected_material,
        "cheapest_found": {
            "supplier": "Lowe's",
            "price": "$8.35/sheet",
            "location": "123 Main St, Sacramento, CA",
            "url": "https://lowes.com/sheetrock-deal"
        },
        "alternatives": [
            {
                "name": "Type X Drywall",
                "benefits": [
                    "Fire resistance",
                    "Meets stairwell and fire code"
                ],
                "price_range": "$9–$11/sheet"
            },
            {
                "name": "Moisture-Resistant Green Board",
                "benefits": [
                    "Good for kitchens and bathrooms",
                    "Mold and mildew resistant"
                ],
                "price_range": "$10–$12/sheet"
            }
        ],
        "recommendation": f"You're currently using {detected_material}. For wet areas, Green Board may offer better protection. For fire-rated zones, Type X is recommended.",
        "message": f"Cheaper {detected_material} available at Lowe’s for $8.35."
    }

    return jsonify(result)
