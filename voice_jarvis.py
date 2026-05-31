import speech_recognition as sr #used to convert microphone speech into text
from gtts import gTTS #used to convert text into realistic mp3 voice
from playsound import playsound #used to play the mp3 file
import os #used to delete temporary audio files
import time #used for unique file naming

from brain.ai_engine import ask_jarvis #imports our ai brain


recognizer = sr.Recognizer() #speech recognizer object


def speak(text): #this function makes jarvis speak anything passed inside text
    print("JARVIS:", text)

    filename = f"jarvis_voice_{int(time.time())}.mp3" #temporary unique audio file

    tts = gTTS(text=text, lang='en')
    tts.save(filename)

    playsound(filename)

    os.remove(filename) #deletes file after speaking


def listen(): #this function activates microphone and listens to the user

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1) #removes background noise
        audio = recognizer.listen(source)

    try:
        user_text = recognizer.recognize_google(audio) #google converts voice to text
        print("You:", user_text)
        return user_text

    except:
        return ""


def run_voice_jarvis():

    speak("Voice mode activated. I am listening.")

    while True: #infinite loop so jarvis keeps listening continuously

        command = listen()

        if command == "":
            continue

        if "stop jarvis" in command.lower() or "goodbye" in command.lower():
            speak("Voice mode shutting down. Goodbye.")
            break

        try:
            reply = ask_jarvis(command) #sends spoken command to ai brain
            speak(reply) #jarvis speaks the answer

        except:
            speak("Gemini request limit has been reached for now. Please try again shortly.")


run_voice_jarvis()