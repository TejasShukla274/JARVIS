# utils/audio_player.py

import sys
import threading
import time

# winsound is built-in on Windows systems
if sys.platform == "win32":
    import winsound
else:
    winsound = None

from voice.voice_output import speak


def play_electronic_beep(frequency=1500, duration=150):
    """
    Synthesizes a simple sound frequency locally on Windows.
    This works completely offline with zero dependency.
    """
    if winsound:
        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            print("Winsound beep error:", e)


def play_futuristic_alarm_async(duration_sec=10, stop_event=None):
    """
    Plays a pulsing electronic alarm sound in a background thread.
    Can be stopped by setting the stop_event.
    """
    def loop():
        elapsed = 0
        while elapsed < duration_sec:
            if stop_event and stop_event.is_set():
                break
                
            # Pulsing high-low synth sound
            play_electronic_beep(1800, 100)
            time.sleep(0.1)
            play_electronic_beep(1200, 100)
            time.sleep(0.3)
            
            elapsed += 0.6
            
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    return thread


def play_notification_beep():
    """
    Futuristic success tone: double high beep.
    """
    def tone():
        play_electronic_beep(2000, 80)
        time.sleep(0.05)
        play_electronic_beep(2500, 120)
    
    threading.Thread(target=tone, daemon=True).start()


def speak_alert(message):
    """
    Speaks an alert message using JARVIS's offline TTS system.
    """
    speak(message)
