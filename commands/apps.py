import webbrowser
import os



# ---------------- WEBSITE COMMANDS ----------------

def open_website(command):

    command = command.lower()



    # OPEN YOUTUBE
    if "open youtube" in command:

        webbrowser.open("https://www.youtube.com")

        return "Opening YouTube"



    # OPEN GOOGLE
    elif "open google" in command:

        webbrowser.open("https://www.google.com")

        return "Opening Google"



    # OPEN SPOTIFY
    elif "open spotify" in command:

        webbrowser.open("https://open.spotify.com")

        return "Opening Spotify"



    return None



# ---------------- LOCAL APPS ----------------

def open_app(command):

    command = command.lower()



    # OPEN CALCULATOR
    if "open calculator" in command:

        os.system("calc")

        return "Opening Calculator"



    # OPEN NOTEPAD
    elif "open notepad" in command:

        os.system("notepad")

        return "Opening Notepad"



    # OPEN CHROME
    elif "open chrome" in command:

        os.system("start chrome")

        return "Opening Chrome"



    return None