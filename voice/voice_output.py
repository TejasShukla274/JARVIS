# voice/voice_output.py

import threading

from gui.gui_state import set_state


# speaking state
is_speaking = False

# lock to serialize pyttsx3 calls (it is not thread-safe)
_tts_lock = threading.Lock()


def speak(text):

    global is_speaking

    if not text:
        return

    def run():

        global is_speaking

        try:

            is_speaking = True

            set_state("speaking")

            print("SPEAKING:", text)

            # Cross-platform TTS using pyttsx3
            # Works on Windows (SAPI5), macOS (NSSpeechSynthesizer), Linux (espeak)
            import pyttsx3

            with _tts_lock:
                engine = pyttsx3.init()
                engine.setProperty('rate', 170)
                engine.setProperty('volume', 1.0)
                engine.say(text)
                engine.runAndWait()

        except Exception as e:

            print("VOICE ERROR:", e)

        finally:

            is_speaking = False

            set_state("idle")

    threading.Thread(
        target=run,
        daemon=True
    ).start()


def stop_speaking():

    global is_speaking

    # pyttsx3 doesn't expose a subprocess to kill,
    # but setting is_speaking = False lets the listener
    # resume immediately after the current utterance finishes.
    is_speaking = False

    set_state("idle")