import requests   #used to send internet requests to news api
import os   #used to access environment variables
import json
import time
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from dotenv import load_dotenv   #used to load api keys from .env file

load_dotenv()   #loads variables from .env

#gets news api key from environment variables
API_KEY = os.getenv("NEWS_API_KEY")

# Caching Paths
DB_DIR = Path(__file__).resolve().parents[1] / "database"
NEWS_CACHE_FILE = DB_DIR / "news_cache.json"
NEWS_IMAGES_DIR = DB_DIR / "news_images"

os.makedirs(NEWS_IMAGES_DIR, exist_ok=True)


def get_news(category="general"):
    #this function fetches category based news
    #example:
    #get_news("sports")
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines?"
            f"country=in&category={category}&apiKey={API_KEY}"
        )

        #sends internet request to news api server
        response = requests.get(url)

        #converts api response into python dictionary/json
        data = response.json()

        #if api fails or key invalid
        if data.get("status") != "ok":
            return "News service is currently unavailable."

        #extracts list of articles
        articles = data.get("articles", [])

        #if no articles found
        if len(articles) == 0:
            return "No news articles were found."

        #stores headlines
        headlines = []

        #gets first headline only
        for article in articles[:1]:
            title = article["title"]
            headlines.append(title)

        #creates final spoken response
        final_news = "Latest news. "

        #adds headlines
        for headline in headlines:
            final_news += f"{headline}. "

        return final_news

    #if internet or api crashes
    except Exception as e:
        print("NEWS ERROR:", e)
        return "Unable to fetch news right now."


def search_news(topic):
    #this function searches news based on custom topic
    #example:
    #search_news("artificial intelligence")
    try:
        url = (
            f"https://newsapi.org/v2/everything?"
            f"q={topic}&sortBy=publishedAt&apiKey={API_KEY}"
        )

        #sends request to news api
        response = requests.get(url)

        #converts response into python dictionary/json
        data = response.json()

        #if api fails
        if data.get("status") != "ok":
            return "Unable to fetch topic news right now."

        #extracts articles list
        articles = data.get("articles", [])

        #if no articles found
        if len(articles) == 0:
            return f"No recent news was found about {topic}."

        #stores top headlines
        headlines = []

        #gets first headline only
        for article in articles[:1]:
            title = article["title"]
            headlines.append(title)

        #creates final response sentence
        final_news = f"Latest news about {topic}. "

        #adds headlines
        for headline in headlines:
            final_news += f"{headline}. "

        return final_news

    #if internet/api crashes
    except Exception as e:
        print("NEWS ERROR:", e)
        return "Topic news service is currently unavailable."


# ── RSS Feed Caching & Offline Parsing System ─────────────────────────────────

def download_image_cache(url):
    """Asynchronously download and cache thumbnails in the local disk directory."""
    if not url:
        return ""
    try:
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        file_path = NEWS_IMAGES_DIR / f"{url_hash}.jpg"
        
        # If it's already downloaded, return local path
        if file_path.exists() and file_path.stat().st_size > 0:
            return str(file_path)
            
        # Download and write
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
            return str(file_path)
    except Exception as e:
        print(f"Error downloading news image {url}: {e}")
    return ""


def fetch_and_cache_news():
    """
    Fetches latest world news from robust RSS feeds and writes to local JSON cache.
    Downloads news images to disk. Extremely lightweight, no third-party XML engines.
    """
    feeds = [
        ("BBC News World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Al Jazeera World", "https://www.aljazeera.com/xml/rss/all.xml")
    ]
    
    parsed_articles = []
    
    for source_name, url in feeds:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code != 200:
                continue
                
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            
            for item in items[:10]:
                headline = item.find("title")
                description = item.find("description")
                link = item.find("link")
                pubDate = item.find("pubDate")
                
                title_text = headline.text if headline is not None else ""
                desc_text = description.text if description is not None else ""
                link_text = link.text if link is not None else ""
                date_text = pubDate.text if pubDate is not None else ""
                
                # Strip HTML from description if any
                if desc_text:
                    import re
                    desc_text = re.sub('<[^<]+?>', '', desc_text).strip()
                
                # Look for media:thumbnail or media:content or enclosure
                thumb_url = ""
                enclosure = item.find("enclosure")
                if enclosure is not None:
                    thumb_url = enclosure.get("url", "")
                else:
                    # Look globally inside children for media namespaces
                    for child in item:
                        if "thumbnail" in child.tag or "content" in child.tag:
                            u = child.get("url")
                            if u:
                                thumb_url = u
                                break
                
                # Fetch publication time cleanly
                time_str = "Recent"
                if date_text:
                    try:
                        # Clean up formatting of pubDate e.g. "Thu, 28 May 2026 03:00:00 GMT"
                        parts = date_text.split(" ")
                        if len(parts) >= 5:
                            time_str = f"{parts[1]} {parts[2]} {parts[4][:5]}"
                    except:
                        time_str = date_text
                        
                local_thumb = ""
                if thumb_url:
                    local_thumb = download_image_cache(thumb_url)
                
                parsed_articles.append({
                    "headline": title_text,
                    "summary": desc_text[:120] + ("..." if len(desc_text) > 120 else "") if desc_text else "No preview available.",
                    "source": source_name,
                    "time": time_str,
                    "thumbnail": local_thumb,
                    "original_thumb_url": thumb_url
                })
        except Exception as e:
            print(f"Error parsing RSS from {source_name}: {e}")
            
    if parsed_articles:
        # Write to JSON Cache
        cache_data = {
            "timestamp": time.time(),
            "articles": parsed_articles
        }
        try:
            with open(NEWS_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=4)
        except Exception as e:
            print(f"Failed to write news cache file: {e}")
        return parsed_articles
        
    return get_cached_news()


def get_cached_news():
    """Reads news from local cache directly. If no cache or invalid, return empty list."""
    if not NEWS_CACHE_FILE.exists():
        return []
    try:
        with open(NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Make sure we have local files valid
            articles = data.get("articles", [])
            for art in articles:
                if art.get("thumbnail") and not Path(art["thumbnail"]).exists():
                    # Fallback to online url or download again
                    art["thumbnail"] = ""
            return articles
    except Exception as e:
        print("Error reading news cache:", e)
        return []


def is_news_cache_expired(max_age_seconds=2700):  # 45 mins
    """Returns True if the news cache doesn't exist or is older than max_age_seconds."""
    if not NEWS_CACHE_FILE.exists():
        return True
    try:
        with open(NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            timestamp = data.get("timestamp", 0)
            return (time.time() - timestamp) > max_age_seconds
    except:
        return True