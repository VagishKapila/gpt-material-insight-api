import os
import requests

def download_weather_icon(icon_code):
    """Download weather icon from wttr.in and return the local file path."""
    icon_map = {
        "☀️": "sun.png",
        "🌧️": "rain.png",
        "☁️": "cloud.png",
        "⛅": "partly_cloudy.png",
        "❄️": "snow.png",
        "🌩️": "storm.png"
    }
    icon_filename = icon_map.get(icon_code.strip(), "weather.png")

    # Local file path
    icon_path = os.path.join("static", "icons", icon_filename)

    # If not found locally, fallback to a placeholder
    if not os.path.exists(icon_path):
        return None

    return icon_path
