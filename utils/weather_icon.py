# utils/weather_icon.py

import requests

def get_weather_icon(location):
    """
    Fetch weather condition from wttr.in and return local icon path
    """
    try:
        if not location:
            return "/static/icons/default.png"

        url = f"https://wttr.in/{location}?format=%C"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return "/static/icons/default.png"

        condition = response.text.strip().lower()

        if "sun" in condition:
            return "/static/icons/sunny.png"
        elif "cloud" in condition:
            return "/static/icons/cloudy.png"
        elif "rain" in condition:
            return "/static/icons/rainy.png"
        elif "snow" in condition:
            return "/static/icons/snowy.png"
        elif "fog" in condition:
            return "/static/icons/foggy.png"
        else:
            return "/static/icons/default.png"

    except Exception as e:
        print(f"[Weather Icon] Error: {e}")
        return "/static/icons/default.png"
