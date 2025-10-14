# Nails & Notes: Construction Daily Log AI (Flask App)

This Flask application powers the backend of Nails & Notes — an AI-powered construction site daily log generator with photo analysis and PDF export.

## Features
- Accepts project metadata and daily log inputs
- Uploads or links to user logos
- Supports material image analysis via `/analyze-image`
- Outputs a 3-page branded PDF:
  - Page 1: Work summary, materials, weather, crew, delays, visitors, safety
  - Page 2: Photos with captions
  - Page 3: AI-generated material recommendation and cost comparison

## Routes
- `GET /` → Simple frontend form for testing log creation
- `POST /generate-pdf` → Creates PDF from daily log info
- `POST /analyze-image` → Accepts image URL and returns material + supplier insight

## How to Run Locally
```bash
pip install -r requirements.txt
python app.py
```

Then go to http://localhost:5000 to test the daily log form.