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
HOST = "127.0.0.1"
PORT = 8765
NOMINATIM_DELAY_SECONDS = 1.1
USER_AGENT = "JARVIS-Maps/1.0 (local personal assistant)"

server = None
server_lock = threading.Lock()
cache_lock = threading.Lock()
last_request_time = 0


def normalize_place(place):
    return " ".join(place.lower().strip().split())


def load_cache():
    if not MAP_CACHE_FILE.exists():
        return {}

    try:
        with open(MAP_CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache):
    MAP_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MAP_CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, indent=4)


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
            "q": place
        },
        headers={
            "User-Agent": USER_AGENT
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


class MapRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(MAPS_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)

        if parsed_url.path == "/api/geocode":
            self.handle_geocode(parsed_url)
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


def open_map(place):
    place = place.strip()

    if not place:
        return "Please tell me which place to show on the map."

    ensure_map_server()

    encoded_place = urllib.parse.quote(place)
    map_url = f"http://{HOST}:{PORT}/?q={encoded_place}"

    webbrowser.open(map_url)

    return f"Opening map of {place}."
