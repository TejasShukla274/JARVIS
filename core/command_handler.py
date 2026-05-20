import datetime
import os

from memory.owner_profile import get_owner_info

from brain.ai_engine import ask_jarvis

from vision.vision_detector import detect_objects

from music.spotify_controller import (
    play_music,
    pause_music,
    next_song,
    previous_song,
    play_specific_song
)

from services.weather_service import get_weather
from services.news_services import search_news

from commands.apps import *


def process_command(user_text):

    # CLEAN USER INPUT
    user_text = user_text.lower().strip()

    print("PROCESSING COMMAND:", user_text)

    # ---------------- WEBSITE COMMANDS ----------------

    website_response = open_website(user_text)

    if website_response:

        return website_response

    # ---------------- APP COMMANDS ----------------

    app_response = open_app(user_text)

    if app_response:

        return app_response

    # ---------------- OWNER QUESTIONS ----------------

    if (
        "who am i" in user_text
        or "my name" in user_text
        or "what's my name" in user_text
    ):

        return f"Your name is {get_owner_info('name')}."

    elif "birthday" in user_text:

        return f"Your birthday is on {get_owner_info('birthday')}."

    elif "where do i live" in user_text:

        return f"You live in {get_owner_info('city')}."

    elif "who created you" in user_text:

        return f"I was created by {get_owner_info('creator')}."

    # ---------------- VISION ----------------

    elif (
        "what do you see" in user_text
        or "what can you see" in user_text
        or "look around" in user_text
    ):

        objects = detect_objects()

        if objects:

            return f"I currently see {', '.join(objects)}."

        else:

            return "I could not detect anything."

    # ---------------- TIME ----------------

    elif (
        "time" in user_text
        or "current time" in user_text
    ):

        current_time = datetime.datetime.now().strftime("%I:%M %p")

        return f"The current time is {current_time}."

    # ---------------- DATE ----------------

    elif "date" in user_text:

        current_date = datetime.datetime.now().strftime("%d %B %Y")

        return f"Today's date is {current_date}."

    # ---------------- SPOTIFY ----------------

    elif "play music" in user_text:

        return play_music()

    elif "pause music" in user_text:

        return pause_music()

    elif "next song" in user_text:

        return next_song()

    elif "previous song" in user_text:

        return previous_song()

    elif user_text.startswith("spotify "):

        song_name = user_text.replace("spotify", "").strip()

        return play_specific_song(song_name)

    # ---------------- WEATHER ----------------

    elif "weather in" in user_text:

        city = user_text.split("weather in")[-1].strip()

        return get_weather(city)

    # ---------------- NEWS ----------------

    elif "news about" in user_text:

        topic = user_text.split("news about")[-1].strip()

        return search_news(topic)

    # ---------------- EXIT ----------------

    elif (
        "shutdown jarvis" in user_text
        or "go offline" in user_text
        or "exit" in user_text
    ):

        os._exit(0)

    # ---------------- AI FALLBACK ----------------

    else:

        return ask_jarvis(user_text)