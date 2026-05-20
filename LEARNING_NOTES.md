## 1 May

Today I learned:

1. How python folders and files are created 
2. Meaning of files 
- md  - This is more organized way 
- txt - To write the normal texts, like a rought notebook
- env - To create an environment
3. Activation of personal environment using "venv\Scripts\activate" 
4. What is pip ?
   It stands for python package installer and has all the libraries
   needed for the python program to run 
5. Creation of venv(Virtual Enviroment) - python -m venv venv
    Stands for - create a python virtual environment named venv


Completed:
 - JARVIS workspace created
 - Installed the required libraries
 - venv installed


## 2 May


Today I learned :

- functions that can handle waiting/network operations efficiently without blocking the whole program.
- how to make a bot on telegram 
- how to add other functions to your telegram



Today I learned:

1. Telegram bots ae created using BotFather and controlled using a unique Bot API token.
2. The Bot API token acts like the password/identity key of the bot.
3. The token is stored securely in the .env file and loaded into Python using load_dotenv().
4. Telegram sends every incoming message as an Update object.
5. CommandHandler handles slash commands like /start.
6. MessageHandler handles normal text messages.
7. async def is used because sending and receiving messages over network takes time, so the bot should wait without freezing.
8. run_polling() keeps checking Telegram servers continuously for new messages.
9. main.py imports run_bot() from telegram_bot.py and starts the whole bot.

Debugging learned:
- A tiny missing () in load_dotenv can break the entire program.





## 3 May

Today I learned:

- how separate python modules communicate with each other
- how telegram messages can be routed into an AI model
- how to use prompt engineering to control AI response length and behavior
- how to handle telegram platform message limits
- built first fully working JARVIS AI telegram bot







# JARVIS Project — Today's Learning Notes

## 4 May
Today's session focused on upgrading JARVIS from a text-based AI bot into a speaking voice assistant.

---

## 1. Voice Assistant Architecture Understood

Today I learned that a real voice assistant is made of multiple connected layers:

- Microphone Input Layer → listens to my voice
- Speech Recognition Layer → converts voice to text
- AI Brain Layer → processes text and generates answer
- Text To Speech Layer → converts answer into spoken audio
- Loop Controller → keeps assistant continuously listening

This means JARVIS is no longer just a Telegram chatbot. It now has an actual conversational voice cycle.

---

## 2. Why pyttsx3 Failed and Why We Switched

Initially we used pyttsx3.

This worked only for startup speech but failed inside continuous microphone loops because:

- Windows SAPI voice engine conflicts with repeated microphone activation
- speech queue freezes after listening cycle

So we replaced it with:

- gTTS = Google Text To Speech
- playsound = audio playback

This method converts JARVIS text into mp3, plays it aloud, and deletes the temporary file.

---

## 3. New Libraries Installed Today

Installed packages:

pip install SpeechRecognition
pip install pyaudio
pip install gTTS
pip install playsound==1.2.2

Purpose:

- SpeechRecognition → voice to text
- PyAudio → microphone access
- gTTS → text to realistic voice
- playsound → play spoken mp3

---

## 4. voice_jarvis.py Main Working Logic

Today's new file created: voice_jarvis.py

This file handles:

listen()
- opens microphone
- captures speech
- converts it into text

speak(text)
- converts Jarvis reply into mp3
- plays it aloud

run_voice_jarvis()
- infinite loop
- keep listening
- send command to AI brain
- speak the reply

This created the full talking assistant.

---

## 5. Gemini Quota Error Learned

I also learned why this error came:

429 RESOURCE_EXHAUSTED

Meaning Gemini free tier has daily request limits.

Every single user sentence was being sent to Gemini, so quota finished quickly.

This taught me that not every small greeting should consume cloud AI.

---

## 6. Local Command Intelligence Concept Learned

We modified brain/ai_engine.py.

Now before sending anything to Gemini:

Python first checks if the command is simple.

Examples:

- hello
- hi
- who are you
- thanks
- good morning

For these:
Python itself returns handcrafted JARVIS replies.

Only difficult educational or intelligent queries are sent to Gemini.

This creates:

- faster replies
- less API usage
- more personal assistant feel

This is the beginning of a local reflex brain.

---

## 7. Biggest Concept Learned Today

A true assistant is not just API key plus chatbot.

A true assistant has:

- local rule engine
- custom personality
- memory
- voice input
- voice output
- cloud intelligence only when required

This was the biggest understanding of today's session.

---

## 8. Current Status of JARVIS After Today

JARVIS can now:

- reply in Telegram
- remember previous conversation
- show typing simulation
- listen through microphone
- speak aloud
- answer local basic commands instantly
- use Gemini for intelligent responses

So this is now a Version 1 desktop voice assistant.

---

## 9. Next Planned Upgrades

Possible next development paths:

- Personal command pack
- Open apps and websites by voice
- File upload and file explanation
- Face recognition
- Mobile app conversion

---

## Conclusion

Today's session was one of the most important milestones in the JARVIS project.

The project shifted from a normal AI text bot into an actual speaking voice assistant.

This was the day JARVIS got its voice.

## 5 May

## 1. Added Owner Memory System

Created memory/owner_profile.py to store Tejas's personal details like:

name
birthday
city
creator

Jarvis can now answer personal questions without using Gemini API.

## 2. Created Central Command Handler

Created core/command_handler.py.

All user commands now go through:

process_command(user_text)

This function checks:

if command is local → Jarvis handles it itself
if command is unknown → sends it to Gemini

Local commands added:

who am i
my birthday
open youtube/google
open calculator/notepad
time/date
exit
## 3. Connected Command Handler with Voice Listener

Updated listener.py so voice commands no longer go directly to Gemini.

New flow:

Voice Input → process_command() → Local Action or Gemini Reply

This gave Jarvis proper command intelligence.

## 4. Fixed Voice Shutdown

Changed shutdown logic from break to return.

Now command:

jarvis exit

fully closes the assistant.

## 5. Upgraded Wake Word System

Old system needed:

jarvis ...pause... command

New system accepts:

jarvis what is the time
jarvis open youtube
jarvis exit

This was done by capturing full speech once and removing the word "jarvis" from the sentence.

Main solving line:

command = heard_text.replace("jarvis", "").strip()

## 6. Added Debugging Prints

Added:

PROCESSING COMMAND:
JARVIS:

to verify whether command handler is working properly.

This helped debug command routing errors.

Current Result

Jarvis now has:

owner memory
local command routing
website/app control
time/date response
voice shutdown
one-line natural wake commands
Gemini fallback

## 6 May

- Spotify account authentication
- direct playback control

- next/previous/pause/resume

- dynamic song search by voice

- zero Gemini usage for music


## 7 May

- Integrated live news system using NewsAPI

- Built news_service.py with modular API architecture

- Added category-based news:
  latest news 
  sports news
  tech news
  business news

- Upgraded to dynamic topic-based news search:
  “news about AI”
  “news about FC Bayern Munich”
  “news about Tesla”
 
 - Problem is that its not giving news of the current time

 ## 18 May

- Gave a real form to my assistant, its not perfect but will surely upgrade it with time.
- Also added a method so that I can stop it while it is speaking

## 19 May

- Now the gui is ready and is giving responses and also changing sizes when hears something

## 20 May

- Made the camera work, now the camera identifies what is there in front of it, 
  and closes when the detection is complete