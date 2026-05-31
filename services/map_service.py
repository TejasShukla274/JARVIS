import json
import pathlib
import threading
import time
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
MAPS_DIR = PROJECT_ROOT / "maps"
MAP_CACHE_FILE = PROJECT_ROOT / "memory" / "map_cache.json"
ROUTE_CACHE_FILE = PROJECT_ROOT / "memory" / "route_cache.json"
HOST = "127.0.0.1"
PORT = 8765
NOMINATIM_DELAY_SECONDS = 1.1
OSRM_DELAY_SECONDS = 1.1
USER_AGENT = "JARVIS-Maps/1.0 (local personal assistant)"

server = None
server_lock = threading.Lock()
cache_lock = threading.Lock()
last_request_time = 0
last_route_request_time = 0
current_view_params = {}


def normalize_place(place):
    return " ".join(place.lower().strip().split())


def load_json(path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_cache():
    return load_json(MAP_CACHE_FILE)


def save_cache(cache):
    save_json(MAP_CACHE_FILE, cache)


def geocode_place(place):
    global last_request_time

    cache_key = normalize_place(place)

    with cache_lock:
        cache = load_cache()

        if cache_key in cache:
            return {
                **cache[cache_key],
                "from_cache": True
            }

    wait_time = NOMINATIM_DELAY_SECONDS - (time.time() - last_request_time)

    if wait_time > 0:
        time.sleep(wait_time)

    last_request_time = time.time()

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "format": "jsonv2",
            "limit": 1,
            "accept-language": "en",
            "q": place
        },
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "en"
        },
        timeout=10
    )

    response.raise_for_status()

    matches = response.json()

    if not matches:
        raise ValueError(f"I could not find {place}.")

    match = matches[0]
    result = {
        "query": place,
        "displayName": match["display_name"],
        "lat": float(match["lat"]),
        "lon": float(match["lon"])
    }

    with cache_lock:
        cache = load_cache()
        cache[cache_key] = result
        save_cache(cache)

    return {
        **result,
        "from_cache": False
    }


def route_cache_key(origin, destination):
    return f"{normalize_place(origin)}::{normalize_place(destination)}"


def format_duration(seconds):
    minutes = round(seconds / 60)
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours and remaining_minutes:
        return f"{hours} hr {remaining_minutes} min"

    if hours:
        return f"{hours} hr"

    return f"{remaining_minutes} min"


def get_route(origin, destination):
    global last_route_request_time

    origin = origin.strip()
    destination = destination.strip()

    if not origin or not destination:
        raise ValueError("Both start and destination are required.")

    cache_key = route_cache_key(origin, destination)

    with cache_lock:
        route_cache = load_json(ROUTE_CACHE_FILE)

        if cache_key in route_cache:
            return {
                **route_cache[cache_key],
                "from_cache": True
            }

    start = geocode_place(origin)
    end = geocode_place(destination)

    wait_time = OSRM_DELAY_SECONDS - (time.time() - last_route_request_time)

    if wait_time > 0:
        time.sleep(wait_time)

    last_route_request_time = time.time()

    coordinates = (
        f"{start['lon']},{start['lat']};"
        f"{end['lon']},{end['lat']}"
    )

    response = requests.get(
        f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
        params={
            "alternatives": "true",
            "steps": "false",
            "geometries": "geojson",
            "overview": "full"
        },
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=20
    )

    response.raise_for_status()
    payload = response.json()

    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise ValueError("I could not find a road route between those places.")

    best_route = min(
        payload["routes"],
        key=lambda route: route.get("duration", float("inf"))
    )
    geometry = best_route["geometry"]["coordinates"]

    result = {
        "origin": start,
        "destination": end,
        "distanceMeters": best_route["distance"],
        "distanceKm": round(best_route["distance"] / 1000, 1),
        "durationSeconds": best_route["duration"],
        "durationText": format_duration(best_route["duration"]),
        "coordinates": [
            {
                "lat": lat,
                "lon": lon
            }
            for lon, lat in geometry
        ]
    }

    with cache_lock:
        route_cache = load_json(ROUTE_CACHE_FILE)
        route_cache[cache_key] = result
        save_json(ROUTE_CACHE_FILE, route_cache)

    return {
        **result,
        "from_cache": False
    }


class MapRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(MAPS_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/api/geocode":
            self.handle_geocode(parsed_url)
            return

        if parsed_url.path == "/api/route":
            self.handle_route(parsed_url)
            return

        if parsed_url.path == "/":
            self.path = "/index.html"

        super().do_GET()

    def handle_geocode(self, parsed_url):
        query = urllib.parse.parse_qs(parsed_url.query)
        place = query.get("q", [""])[0].strip()

        if not place:
            self.send_json(
                {"error": "Missing place query."},
                status=400
            )
            return

        try:
            self.send_json(geocode_place(place))
        except ValueError as error:
            self.send_json(
                {"error": str(error)},
                status=404
            )
        except Exception:
            self.send_json(
                {"error": "Map search is unavailable right now."},
                status=503
            )

    def handle_route(self, parsed_url):
        query = urllib.parse.parse_qs(parsed_url.query)
        origin = query.get("from", [""])[0].strip()
        destination = query.get("to", [""])[0].strip()

        if not origin or not destination:
            self.send_json(
                {"error": "Missing route start or destination."},
                status=400
            )
            return

        try:
            self.send_json(get_route(origin, destination))
        except ValueError as error:
            self.send_json(
                {"error": str(error)},
                status=404
            )
        except Exception:
            self.send_json(
                {"error": "Route service is unavailable right now."},
                status=503
            )

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def ensure_map_server():
    global server

    with server_lock:
        if server:
            return

        server = ThreadingHTTPServer(
            (HOST, PORT),
            MapRequestHandler
        )

        threading.Thread(
            target=server.serve_forever,
            daemon=True
        ).start()


def view_url(params):
    return f"http://{HOST}:{PORT}/?{urllib.parse.urlencode(params)}"


def open_map(place, mode="2d"):
    global current_view_params

    place = place.strip()
    mode = mode.strip().lower() or "2d"

    if not place:
        return "Please tell me which place to show on the map."

    ensure_map_server()

    current_view_params = {
        "q": place,
        "mode": mode
    }

    map_url = view_url(current_view_params)

    webbrowser.open(map_url)

    return f"Opening {mode.upper()} map of {place}."


def open_route(origin, destination, mode="2d"):
    global current_view_params

    origin = origin.strip()
    destination = destination.strip()
    mode = mode.strip().lower() or "2d"

    if not origin or not destination:
        return "Please tell me both the start and destination."

    ensure_map_server()

    current_view_params = {
        "from": origin,
        "to": destination,
        "mode": mode
    }

    map_url = view_url(current_view_params)

    webbrowser.open(map_url)

    return f"Opening the smartest {mode.upper()} route from {origin} to {destination}."


def zoom_map(direction):
    direction = direction.strip().lower()

    if direction not in {"in", "out"}:
        return "Please say zoom in or zoom out."

    ensure_map_server()

    params = current_view_params.copy() or {
        "q": "world",
        "mode": "2d"
    }
    params["zoom"] = direction

    webbrowser.open(view_url(params))

    return f"Zooming {direction} on the map."
