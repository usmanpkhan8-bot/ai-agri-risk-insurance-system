# ============================================================
#  FILE: weather_api.py
#  WHAT THIS FILE DOES:
#  Fetches LIVE real-time weather for any Indian district
#  using Open-Meteo API — completely FREE, no API key needed!
#
#  Used by app.py to get current weather automatically
# ============================================================

import requests

import json
import os

# Load large pre-geocoded map of Indian districts
coords_path = os.path.join(os.path.dirname(__file__), "outputs", "district_coords.json")
try:
    with open(coords_path, "r") as f:
        DISTRICT_COORDS = json.load(f)
except Exception:
    DISTRICT_COORDS = {}


def get_live_weather(district_name):
    """
    Fetches current weather for a given district.
    Returns a dictionary with weather details.
    If district not found or API fails, returns safe default values.
    """

    district_upper = district_name.upper().strip()

    # Check if we have manually defined coordinates
    if district_upper in DISTRICT_COORDS:
        coords = DISTRICT_COORDS[district_upper]
        lat    = coords["lat"]
        lon    = coords["lon"]
        state  = coords.get("state", "India")
    else:
        # Dynamically fetch coordinates from Open-Meteo Geocoding API!
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={district_name}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=5)
            geo_res.raise_for_status()
            geo_data = geo_res.json()
            if "results" in geo_data and len(geo_data["results"]) > 0:
                result = geo_data["results"][0]
                lat    = result.get("latitude")
                lon    = result.get("longitude")
                state  = result.get("admin1", "India") # admin1 is usually state
            else:
                raise ValueError("Location not found in Geocoding API")
        except Exception as e:
            return {
                "found":       False,
                "district":    district_name,
                "message":     "Coordinates not available for this district",
                "temperature": None,
                "rainfall":    None,
                "humidity":    None,
                "wind_speed":  None,
                "condition":   "Unknown",
            }

    # Open-Meteo API URL — free, no key needed!
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,"
        f"precipitation,wind_speed_10m,weather_code"
        f"&timezone=Asia/Kolkata"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data    = response.json()
        current = data["current"]

        temp      = current.get("temperature_2m", 0)
        humidity  = current.get("relative_humidity_2m", 0)
        rainfall  = current.get("precipitation", 0)
        wind      = current.get("wind_speed_10m", 0)
        wcode     = current.get("weather_code", 0)

        # Convert weather code to human readable condition
        condition = weather_code_to_text(wcode)

        # Determine weather risk for crops
        weather_risk = assess_weather_risk(temp, rainfall, humidity)

        return {
            "found":        True,
            "district":     district_name,
            "state":        state,
            "temperature":  round(temp, 1),
            "humidity":     round(humidity, 1),
            "rainfall":     round(rainfall, 1),
            "wind_speed":   round(wind, 1),
            "condition":    condition,
            "weather_risk": weather_risk,
            "lat":          lat,
            "lon":          lon,
        }

    except Exception as e:
        return {
            "found":       False,
            "district":    district_name,
            "message":     f"Could not fetch weather: {str(e)}",
            "temperature": None,
            "rainfall":    None,
            "humidity":    None,
            "wind_speed":  None,
            "condition":   "Unavailable",
        }


def weather_code_to_text(code):
    """Converts Open-Meteo weather code to readable text."""
    if code == 0:               return "☀️ Clear Sky"
    elif code in [1, 2, 3]:    return "⛅ Partly Cloudy"
    elif code in [45, 48]:     return "🌫️ Foggy"
    elif code in [51, 53, 55]: return "🌦️ Drizzle"
    elif code in [61, 63, 65]: return "🌧️ Rain"
    elif code in [71, 73, 75]: return "❄️ Snow"
    elif code in [80, 81, 82]: return "🌧️ Heavy Rain Showers"
    elif code in [95, 96, 99]: return "⛈️ Thunderstorm"
    else:                       return "🌤️ Mixed Conditions"


def assess_weather_risk(temp, rainfall, humidity):
    """
    Simple rule-based weather risk assessment for crops.
    Returns: HIGH / MEDIUM / LOW with reason
    """
    if temp > 40:
        return {"level": "HIGH",   "reason": "Extreme heat stress for crops"}
    elif temp > 35 and rainfall < 1:
        return {"level": "HIGH",   "reason": "High temperature + no rainfall"}
    elif rainfall > 50:
        return {"level": "HIGH",   "reason": "Excess rainfall may damage crops"}
    elif temp < 10:
        return {"level": "MEDIUM", "reason": "Cold stress possible"}
    elif humidity > 90:
        return {"level": "MEDIUM", "reason": "High humidity — disease risk"}
    elif temp > 30 and rainfall < 5:
        return {"level": "MEDIUM", "reason": "Warm and dry conditions"}
    else:
        return {"level": "LOW",    "reason": "Weather conditions are normal"}


# ────────────────────────────────────────────
# TEST IT DIRECTLY
# Run: python weather_api.py
# ────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing Live Weather API...\n")

    test_districts = ["NAMAKKAL", "PUNE", "LUDHIANA"]

    for district in test_districts:
        weather = get_live_weather(district)
        print(f"District: {district}")
        if weather["found"]:
            print(f"  🌡️  Temperature: {weather['temperature']}°C")
            print(f"  💧 Humidity:    {weather['humidity']}%")
            print(f"  🌧️  Rainfall:    {weather['rainfall']} mm")
            print(f"  💨 Wind Speed:  {weather['wind_speed']} km/h")
            print(f"  🌤️  Condition:   {weather['condition']}")
            print(f"  ⚠️  Crop Risk:   {weather['weather_risk']['level']} — {weather['weather_risk']['reason']}")
        else:
            print(f"  ❌ {weather['message']}")
        print()