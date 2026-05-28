import requests   #used to send internet requests to weather api
import os   #used to access environment variables
import json
import time
from pathlib import Path
from dotenv import load_dotenv   #used to load hidden api keys from env file

load_dotenv()   #loads all variables from .env file

#gets weather api key from env file
API_KEY = os.getenv("WEATHER_API_KEY")

DB_DIR = Path(__file__).resolve().parents[1] / "database"
WEATHER_CACHE_FILE = DB_DIR / "weather_cache.json"


def get_weather(city):
    #this function receives city name from jarvis command
    #example:
    #get_weather("delhi")
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={API_KEY}&units=metric"
        )

        response = requests.get(url)

        #converts api response into python dictionary/json format
        data = response.json()
        print(data)

        if data.get("cod") != 200:
            return "I could not find that city."

        # ---------------- EXTRACTING WEATHER DATA ----------------
        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"]

        return (
            f"The current temperature in {city} is {temperature} degrees Celsius "
            f"with {condition}. "
            f"It feels like {feels_like} degrees "
            f"and humidity is {humidity} percent."
        )

    #if internet fails or api crashes this runs
    except Exception as e:
        print("WEATHER ERROR:", e)
        return "Weather service is currently unavailable."


# ── Weather Caching & Categorization System ───────────────────────────────────

def fetch_and_cache_weather(city="Delhi"):
    """
    Fetches live weather for specified city and updates the local JSON cache.
    Classifies conditions into standard categories to map to HUD animation layers.
    """
    if not API_KEY:
        print("No WEATHER_API_KEY found.")
        return get_cached_weather()
        
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={API_KEY}&units=metric"
        )
        response = requests.get(url, timeout=8)
        data = response.json()
        
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            condition = data["weather"][0]["description"].title()
            weather_main = data["weather"][0]["main"].lower()
            
            # Map condition string to animation categories
            # categories: clear_day, clear_night, clouds, rain, thunderstorm, snow, mist
            icon_category = "clouds"
            w_lower = weather_main.lower()
            if "clear" in w_lower:
                # determine day/night using sunrise/sunset
                sys_data = data.get("sys", {})
                current_time = time.time()
                sunrise = sys_data.get("sunrise", 0)
                sunset = sys_data.get("sunset", 0)
                if sunrise < current_time < sunset:
                    icon_category = "clear_day"
                else:
                    icon_category = "clear_night"
            elif "cloud" in w_lower:
                icon_category = "clouds"
            elif any(x in w_lower for x in ["rain", "drizzle", "shower"]):
                icon_category = "rain"
            elif "thunder" in w_lower:
                icon_category = "thunderstorm"
            elif "snow" in w_lower:
                icon_category = "snow"
            elif any(x in w_lower for x in ["mist", "haze", "fog", "smoke", "dust", "sand"]):
                icon_category = "mist"
                
            cache_data = {
                "timestamp": time.time(),
                "city": city.title(),
                "temperature": round(temp, 1),
                "feels_like": round(feels_like, 1),
                "humidity": humidity,
                "condition": condition,
                "icon": icon_category
            }
            
            with open(WEATHER_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=4)
                
            return cache_data
            
    except Exception as e:
        print(f"Error fetching weather for caching: {e}")
        
    return get_cached_weather()


def get_cached_weather():
    """Reads cached weather from disk. If no cache exists, returns None."""
    if not WEATHER_CACHE_FILE.exists():
        return None
    try:
        with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error reading weather cache:", e)
        return None


def is_weather_cache_expired(max_age_seconds=1500):  # 25 mins
    """Returns True if cache is non-existent or stale."""
    if not WEATHER_CACHE_FILE.exists():
        return True
    try:
        with open(WEATHER_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            timestamp = data.get("timestamp", 0)
            return (time.time() - timestamp) > max_age_seconds
    except:
        return True