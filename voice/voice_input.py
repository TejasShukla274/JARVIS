import speech_recognition as sr   #speech recognition library converts microphone voice into text


def listen_command():   #this function is used after jarvis wakes up to hear the actual command

    recognizer = sr.Recognizer()   #creates recognizer object that understands sound patterns

    with sr.Microphone() as source:   #opens microphone as audio source
        print("Listening...")
        audio = recognizer.listen(source)   #records whatever user says

    try:
        command = recognizer.recognize_google(audio)   #sends audio to google speech engine and gets text
        return command.lower()   #returns text in lower case for easy matching

    except:
        return ""   #if voice not understood returns empty text