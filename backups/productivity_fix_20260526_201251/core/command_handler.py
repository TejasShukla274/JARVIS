import datetime
import os
import re

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
from services.map_service import open_map, open_route, zoom_map
from services.reminder_service import (
    create_reminder_from_command,
    delete_reminder_from_command,
    format_upcoming_reminders
)

from commands.apps import *


def parse_duration_seconds(text):
    patterns = [
        r"\b(?:start|set|create|run)\s+(?:a\s+)?(?:countdown\s+)?timer\s+(?:for|of)?\s*(\d+)\s*(second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs)?\b",
        r"\b(?:start|set|create|run)\s+(?:a\s+)?(\d+)\s*(second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs)\s+(?:countdown\s+)?timer\b",
        r"\b(\d+)\s*(second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs)\s+timer\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if not match:
            continue

        value = int(match.group(1))
        unit = match.group(2)

        if not unit:
            return None

        if unit.startswith(("sec", "second")):
            return value

        if unit.startswith(("min", "minute")):
            return value * 60

        return value * 3600

    return None


def start_countdown_from_command(user_text):
    seconds = parse_duration_seconds(user_text)

    if seconds is None:
        return "Please specify the timer duration, for example: start a timer for 5 seconds."

    from gui.dashboard_window import get_dashboard_window
    from scheduler.background_scheduler import get_scheduler
    from PyQt5.QtCore import QTimer
    import uuid

    timer_id = str(uuid.uuid4())
    label = f"Timer ({seconds}s)" if seconds < 60 else f"Timer ({seconds // 60}m)"

    get_scheduler().start_timer(timer_id, seconds, label)

    QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
    QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(5))
    QTimer.singleShot(80, lambda: get_dashboard_window().tab_stopwatch.refresh_timer_queue())

    return f"Starting a countdown timer for {seconds} seconds."


def process_command(user_text):

    import re
    user_text = user_text.lower().strip()

    print("PROCESSING COMMAND:", user_text)

    # ==================================================
    # OFFLINE SQLITE REMINDERS
    # ==================================================

    if (
        user_text.startswith("remind me")
        or user_text.startswith("set reminder")
        or user_text.startswith("create a reminder")
        or user_text.startswith("add reminder")
    ):

        return create_reminder_from_command(user_text)

    if (
        user_text.startswith("delete reminder")
        or user_text.startswith("delete the reminder")
        or user_text.startswith("remove reminder")
        or user_text.startswith("remove the reminder")
    ):

        return delete_reminder_from_command(user_text)

    if (
        "show reminders" in user_text
        or "list reminders" in user_text
        or "upcoming reminders" in user_text
        or "open reminders" in user_text
    ):

        return format_upcoming_reminders()

    # ==================================================
    # STOPWATCH / TIMER / ALARMS
    # ==================================================

    if "stopwatch" in user_text:

        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer

        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(5))

        if any(word in user_text for word in ["start", "starting", "run"]):
            QTimer.singleShot(80, lambda: get_dashboard_window().tab_stopwatch.start_stopwatch())
            return "Starting the stopwatch chronometer, Sir."

        if any(word in user_text for word in ["pause", "stop"]):
            QTimer.singleShot(80, lambda: get_dashboard_window().tab_stopwatch.pause_stopwatch())
            return "Pausing the stopwatch chronometer, Sir."

        if "reset" in user_text:
            QTimer.singleShot(80, lambda: get_dashboard_window().tab_stopwatch.reset_stopwatch())
            return "Resetting the stopwatch chronometer, Sir."

        return "Opening the stopwatch chronometer, Sir."

    if "timer" in user_text and any(
        word in user_text
        for word in ["start", "set", "create", "run"]
    ):

        return start_countdown_from_command(user_text)

    if (
        "set alarm" in user_text
        or "set an alarm" in user_text
        or "create alarm" in user_text
        or "create an alarm" in user_text
    ):

        from utils.nlp_parser import parse_alarm_nlp
        from database.db_manager import add_alarm
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer

        time_str, label = parse_alarm_nlp(user_text)

        if not time_str:
            return "Could you specify the target alarm time, Sir?"

        add_alarm(time=time_str, label=label, repeat_days="[]", is_active=1)

        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(4))

        return f"Understood. Alarm registered for {time_str} labeled {label}, Sir."

    if (
        user_text.startswith("delete alarm")
        or user_text.startswith("delete the alarm")
        or user_text.startswith("remove alarm")
        or user_text.startswith("remove the alarm")
    ):

        from utils.nlp_parser import parse_alarm_nlp
        from database.db_manager import delete_alarm, get_alarms
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer

        time_str, _ = parse_alarm_nlp(user_text)

        if not time_str:
            return "Which alarm should I delete? Please specify the time."

        deleted_count = 0

        for alarm in get_alarms():
            if alarm["time"] == time_str:
                delete_alarm(alarm["id"])
                deleted_count += 1

        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(4))

        if deleted_count == 0:
            return f"I could not find an alarm for {time_str}."

        return f"Deleted {deleted_count} alarm for {time_str}."

    # =========================================================================
    # PRODUCTIVITY & TIME-MANAGEMENT SUITE INTEGRATION (100% OFFLINE)
    # =========================================================================
    
    # 1. Open Dashboard / Cockpit
    if (
        "open dashboard" in user_text 
        or "show productivity" in user_text 
        or "productivity cockpit" in user_text
    ):
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(0))
        return "Opening the productivity cockpit dashboard, Sir."

    # 2. Open Calendar
    elif "open calendar" in user_text or "show calendar" in user_text:
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(1))
        return "Accessing your calendar ledger now, Sir."

    # 3. Tasks / Kanban board
    elif (
        "open tasks" in user_text 
        or "show task" in user_text
        or "show tasks" in user_text 
        or "kanban" in user_text
    ):
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(2))
        return "Opening task schematics board, Sir."

    # 4. Reminders
    elif "open reminders" in user_text or "show reminders" in user_text:
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(3))
        return "Opening reminders logs, Sir."

    # 5. Alarms
    elif "open alarms" in user_text or "show alarms" in user_text:
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(4))
        return "Opening alarm configuration panels, Sir."

    # 6. Stopwatch & Timers
    elif (
        "open stopwatch" in user_text 
        or "open timer" in user_text 
        or "start stopwatch" in user_text
    ):
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(5))
        if "start stopwatch" in user_text:
            QTimer.singleShot(80, lambda: get_dashboard_window().tab_stopwatch.toggle_stopwatch())
            return "Starting the stopwatch chronometer, Sir."
        return "Opening chronos and countdown timers, Sir."

    # 7. Timer setups (e.g. "start a 10 minute timer", "start a 5 second timer")
    elif "start a " in user_text and " timer" in user_text:
        match = re.search(
            r'start a (\d+)\s*(minute|minutes|min|mins|second|seconds|sec|secs|hour|hours|hr|hrs)\b', 
            user_text
        )
        if match:
            val = int(match.group(1))
            unit = match.group(2).lower()
            
            if "min" in unit:
                secs = val * 60
                label = f"Timer ({val}m)"
            elif "sec" in unit:
                secs = val
                label = f"Timer ({val}s)"
            else:
                secs = val * 3600
                label = f"Timer ({val}h)"
                
            from gui.dashboard_window import get_dashboard_window
            from scheduler.background_scheduler import get_scheduler
            import uuid
            from PyQt5.QtCore import QTimer
            
            tid = str(uuid.uuid4())
            get_scheduler().start_timer(tid, secs, label)
            
            QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
            QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(5))
            
            return f"Understood, starting a {val} {unit} countdown, Sir."

    # 8. Conversational Alarm Setting
    elif "set alarm" in user_text or "create alarm" in user_text:
        from utils.nlp_parser import parse_alarm_nlp
        from database.db_manager import add_alarm
        time_str, label = parse_alarm_nlp(user_text)
        if time_str:
            add_alarm(time=time_str, label=label, repeat_days="[]", is_active=1)
            from gui.dashboard_window import get_dashboard_window
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
            QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(4))
            return f"Understood. Alarm registered for {time_str} labeled {label}, Sir."
        else:
            return "Could you specify the target alarm time, Sir?"

    # 9. Conversational Reminder Setting
    elif (
        "remind me to" in user_text 
        or "create a reminder" in user_text 
        or "add reminder" in user_text
    ):
        from utils.nlp_parser import parse_reminder_nlp
        from database.db_manager import add_reminder
        label, parsed_dt = parse_reminder_nlp(user_text)
        dt_str = parsed_dt.strftime("%d %B at %I:%M %p")
        add_reminder(
            text=label, 
            datetime_str=parsed_dt.isoformat(), 
            category="General", 
            priority="Medium", 
            recurrence="None"
        )
        
        from gui.dashboard_window import get_dashboard_window
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
        QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(3))
        return f"Confirming reminder registered: {label} scheduled for {dt_str}, Sir."

    # 10. Conversational Task Creation
    elif "add task" in user_text or "at task" in user_text or "create task" in user_text:
        title = (
            user_text.replace("add task", "")
            .replace("at task", "")
            .replace("create task", "")
            .strip()
            .capitalize()
        )
        if title:
            from database.db_manager import add_task
            add_task(
                title=title, 
                description="Registered via voice command", 
                priority="Medium", 
                status="todo"
            )
            from gui.dashboard_window import get_dashboard_window
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: get_dashboard_window().showNormal())
            QTimer.singleShot(0, lambda: get_dashboard_window().switch_tab(2))
            return f"Task deployed to schematics board: {title}, Sir."
        else:
            return "Could you please specify the task title, Sir?"

    close_response = close_app(user_text)

    if close_response:

        return close_response

    # ==================================================
    # MAP ZOOM
    # ==================================================

    if "zoom in" in user_text:

        return zoom_map("in")

    if "zoom out" in user_text:

        return zoom_map("out")

    # ==================================================
    # MAP MODE
    # ==================================================

    map_mode = "2d"

    if "4d" in user_text:

        map_mode = "4d"

    elif "3d" in user_text:

        map_mode = "3d"

    # ==================================================
    # ROUTES
    # ==================================================

    route_triggers = [
        "smartest route from",
        "best route from",
        "route from",
        "directions from",
        "distance from",
        "get from",
        "go from",
        "travel from"
    ]

    for trigger in route_triggers:

        if trigger in user_text and " to " in user_text:

            route_text = user_text.split(trigger, 1)[-1].strip()
            origin, destination = route_text.split(" to ", 1)

            return open_route(origin, destination, map_mode)

    # ==================================================
    # MAPS
    # ==================================================

    map_triggers = [
        "show map of",
        "open map of",
        "map of",
        "show me map of",
        "where is",
        "locate"
    ]

    for trigger in map_triggers:

        if trigger in user_text:

            place = user_text.split(trigger, 1)[-1].strip()

            return open_map(place, map_mode)

    # ==================================================
    # OPEN WEBSITES
    # ==================================================

    website_response = open_website(user_text)

    if website_response:

        return website_response

    # ==================================================
    # YOUTUBE SEARCH
    # ==================================================

    youtube_response = play_youtube(user_text)

    if youtube_response:

        return youtube_response

    # ==================================================
    # GOOGLE SEARCH
    # ==================================================

    article_response = open_article(user_text)

    if article_response:

        return article_response

    # ==================================================
    # OPEN APPS
    # ==================================================

    app_response = open_app(user_text)

    if app_response:

        return app_response

    # ==================================================
    # OWNER QUESTIONS
    # ==================================================

    if "who am i" in user_text:

        return f"Your name is {get_owner_info('name')}."

    elif "birthday" in user_text:

        return f"Your birthday is on {get_owner_info('birthday')}."

    elif "where do i live" in user_text:

        return f"You live in {get_owner_info('city')}."

    elif "who created you" in user_text:

        return f"I was created by {get_owner_info('creator')}."

    # ==================================================
    # VISION
    # ==================================================

    elif (
        "what do you see" in user_text
        or "look around" in user_text
    ):

        objects = detect_objects()

        if objects:

            return f"I currently see {', '.join(objects)}."

        else:

            return "I could not detect anything."

    # ==================================================
    # TIME
    # ==================================================

    elif "time" in user_text:

        current_time = datetime.datetime.now().strftime("%I:%M %p")

        return f"The current time is {current_time}."

    # ==================================================
    # DATE
    # ==================================================

    elif "date" in user_text:

        current_date = datetime.datetime.now().strftime("%d %B %Y")

        return f"Today's date is {current_date}."

    # ==================================================
    # SPOTIFY
    # ==================================================

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

    # ==================================================
    # WEATHER
    # ==================================================

    elif "weather in" in user_text:

        city = user_text.split("weather in")[-1].strip()

        return get_weather(city)

    # ==================================================
    # NEWS
    # ==================================================

    elif "news about" in user_text:

        topic = user_text.split("news about")[-1].strip()

        return search_news(topic)

    # ==================================================
    # EXIT
    # ==================================================

    elif (
        "shutdown jarvis" in user_text
        or "go offline" in user_text
        or "exit" in user_text
    ):

        os._exit(0)

    # ==================================================
    # AI FALLBACK
    # ==================================================

    return ask_jarvis(user_text)
