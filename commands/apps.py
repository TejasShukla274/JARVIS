import webbrowser
import os
import urllib.parse


# ==================================================
# OPEN WEBSITES
# ==================================================

def open_website(command):

    command = command.lower().strip()

    websites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "spotify": "https://open.spotify.com",
        "github": "https://github.com",
        "chatgpt": "https://chat.openai.com"
    }

    for site in websites:

        if f"open {site}" in command:

            webbrowser.open(websites[site])

            return f"Opening {site}"

    return None


# ==================================================
# PLAY YOUTUBE VIDEOS
# ==================================================

def play_youtube(command):

    command = command.lower().strip()

    youtube_keywords = [
        "youtube",
        "video",
        "videos",
        "song",
        "music",
        "vlog",
        "watch",
        "play"
    ]

    # MUST CONTAIN VIDEO-TYPE WORDS
    if any(word in command for word in youtube_keywords):

        query = command

        remove_words = [
            "play",
            "open",
            "youtube",
            "video",
            "videos",
            "on youtube",
            "about",
            "watch",
            "show me",
            "search"
        ]

        for word in remove_words:

            query = query.replace(word, "")

        query = query.strip()

        # EMPTY QUERY
        if not query:

            webbrowser.open("https://www.youtube.com")

            return "Opening YouTube"

        encoded_query = urllib.parse.quote(query)

        # OPEN SEARCH PAGE
        url = (
            f"https://www.youtube.com/results?search_query={encoded_query}"
        )

        webbrowser.open(url)

        return f"Opening YouTube videos for {query}"

    return None


# ==================================================
# GOOGLE SEARCH / ARTICLES
# ==================================================

def open_article(command):

    command = command.lower().strip()

    triggers = [
        "article",
        "search",
        "google",
        "tell me about",
        "what is",
        "who is"
    ]

    if any(word in command for word in triggers):

        query = command

        remove_words = [
            "open",
            "article",
            "about",
            "search",
            "google",
            "tell me about",
            "what is",
            "who is"
        ]

        for word in remove_words:

            query = query.replace(word, "")

        query = query.strip()

        if query:

            encoded_query = urllib.parse.quote(query)

            url = (
                f"https://www.google.com/search?q={encoded_query}"
            )

            webbrowser.open(url)

            return f"Searching Google for {query}"

    return None


# ==================================================
# OPEN APPS
# ==================================================

def open_app(command):

    command = command.lower().strip()

    # CALCULATOR
    if "open calculator" in command:

        os.system("start calc")

        return "Opening Calculator"

    # NOTEPAD
    elif "open notepad" in command:

        os.system("start notepad")

        return "Opening Notepad"

    # CHROME
    elif "open chrome" in command:

        os.system("start chrome")

        return "Opening Chrome"

    # PAINT
    elif "open paint" in command:

        os.system("start mspaint")

        return "Opening Paint"

    # VS CODE
    elif "open vs code" in command:

        os.system("code")

        return "Opening VS Code"

    return None


# ==================================================
# CLOSE APPS
# ==================================================

def close_app(command):

    command = command.lower().strip()

    # ==================================================
    # CLOSE YOUTUBE
    # ==================================================

    if "close youtube" in command:

        # CLOSE CHROME
        os.system(
            "taskkill /f /im chrome.exe >nul 2>&1"
        )

        # CLOSE EDGE
        os.system(
            "taskkill /f /im msedge.exe >nul 2>&1"
        )

        return "Closing browser running YouTube"

    # ==================================================
    # CLOSE CHROME
    # ==================================================

    elif "close chrome" in command:

        os.system(
            "taskkill /f /im chrome.exe >nul 2>&1"
        )

        return "Closing Chrome"

    # ==================================================
    # CLOSE EDGE
    # ==================================================

    elif (
        "close edge" in command
        or "close microsoft edge" in command
    ):

        os.system(
            "taskkill /f /im msedge.exe >nul 2>&1"
        )

        return "Closing Microsoft Edge"

    # ==================================================
    # CLOSE NOTEPAD
    # ==================================================

    elif "close notepad" in command:

        os.system(
            "taskkill /f /im notepad.exe >nul 2>&1"
        )

        return "Closing Notepad"

    # ==================================================
    # CLOSE PAINT
    # ==================================================

    elif "close paint" in command:

        os.system(
            "taskkill /f /im mspaint.exe >nul 2>&1"
        )

        return "Closing Paint"

    # ==================================================
    # CLOSE VS CODE
    # ==================================================

    elif "close vs code" in command:

        os.system(
            "taskkill /f /im Code.exe >nul 2>&1"
        )

        return "Closing VS Code"

    # ==================================================
    # CLOSE CALCULATOR
    # ==================================================

    elif "close calculator" in command:

        # OLD WINDOWS CALCULATOR
        os.system(
            "taskkill /f /im CalculatorApp.exe >nul 2>&1"
        )

        # SOME WINDOWS VERSIONS
        os.system(
            "taskkill /f /im calculator.exe >nul 2>&1"
        )

        return "Closing Calculator"

    return None