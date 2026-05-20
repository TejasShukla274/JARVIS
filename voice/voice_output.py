# voice/voice_output.py

import subprocess
import threading

from gui.gui_state import set_state


# speaking state
is_speaking = False

# current process
current_process = None


def speak(text):

    global is_speaking
    global current_process

    if not text:
        return

    def run():

        global is_speaking
        global current_process

        try:

            is_speaking = True

            set_state("speaking")

            print("SPEAKING:", text)

            # Windows native TTS
            command = f'''
Add-Type -AssemblyName System.Speech;
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer;
$speak.Rate = 1;
$speak.Volume = 100;
$speak.Speak("{text}");
'''

            current_process = subprocess.Popen(
                [
                    "powershell",
                    "-Command",
                    command
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            current_process.wait()

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

    global current_process
    global is_speaking

    try:

        if current_process:

            current_process.terminate()

    except:
        pass

    is_speaking = False

    set_state("idle")