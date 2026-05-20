# listener.py

import speech_recognition as sr
import os
import time

from voice.voice_output import (
    speak,
    stop_speaking,
    is_speaking
)

from core.command_handler import process_command

from gui.gui_state import set_state


def wake_listener():

    recognizer = sr.Recognizer()

    print("JARVIS Wake listener activated...")

    speak("Wake listener activated.")

    while True:

        try:

            # do not listen while speaking
            if is_speaking:

                time.sleep(0.1)

                continue

            # open microphone only when needed
            with sr.Microphone() as source:

                set_state("listening")

                print("Waiting for wake word...")

                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.3
                )

                audio = recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=8
                )

            # microphone released here
            set_state("idle")

            heard_text = recognizer.recognize_google(audio).lower()

            print("Heard:", heard_text)

            # wake word detection
            if "jarvis" in heard_text:

                # interrupt speech instantly
                stop_speaking()

                # remove wake word
                command = heard_text.replace(
                    "jarvis",
                    ""
                ).strip()

                if command == "":
                    continue

                print("You:", command)

                response = process_command(command)

                print("JARVIS:", response)

                # ---------------- EXIT COMMAND ----------------

                if response == "EXIT":

                    speak("Going offline now.")

                    # allow speech thread to start
                    time.sleep(0.3)

                    # wait until speaking finishes
                    while is_speaking:

                        time.sleep(0.1)

                    os._exit(0)

                # ---------------- NORMAL RESPONSE ----------------

                speak(response)

        except Exception as e:

            print("FULL ERROR:", repr(e))

            continue