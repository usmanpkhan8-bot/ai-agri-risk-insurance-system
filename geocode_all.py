import time
import json
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor

df = pd.read_csv("outputs/final_insurance_report.csv")
districts = sorted(df['District_Name'].unique().tolist())

coords_cache = {}

def geocode_district(d):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={d}&count=1&language=en&format=json"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            lat = result.get("latitude")
            lon = result.get("longitude")
            state = result.get("admin1", "India")
            
            return d, lat, lon, state
        else:
            print(f"FAILED: {d} not found in geocode")
            return d, None, None, None
    except Exception as e:
        print(f"FAILED: {d} exception {str(e)}")
        return d, None, None, None

print(f"Starting geocode for {len(districts)} districts...")
start = time.time()

with ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(geocode_district, districts))

for d, lat, lon, state in results:
    if lat is not None:
        coords_cache[d.upper()] = {"lat": lat, "lon": lon, "state": state}

# Adding manual fallbacks for the ones that might fail or be generic
coords_cache["NICOBARS"] = {"lat": 7.0, "lon": 93.8, "state": "Andaman & Nicobar"}
coords_cache["NORTH AND MIDDLE ANDAMAN"] = {"lat": 12.5, "lon": 92.8, "state": "Andaman & Nicobar"}
coords_cache["SOUTH ANDAMANS"] = {"lat": 11.6, "lon": 92.7, "state": "Andaman & Nicobar"}

with open("outputs/district_coords.json", "w") as f:
    json.dump(coords_cache, f, indent=4)

print(f"Successfully geocoded {len(coords_cache)} districts in {time.time() - start:.2f} seconds!")
