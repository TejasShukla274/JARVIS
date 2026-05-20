from google import genai
from google.genai import types

from dotenv import load_dotenv

import os

load_dotenv()

# API KEY
GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

# GEMINI CLIENT
client = genai.Client(
    api_key=GEMINI_API_KEY
)


def ask_jarvis(prompt):

    user_input = prompt.lower().strip()

    # --------------------------------
    # SIMPLE OFFLINE RESPONSES
    # --------------------------------

    if (
        "hello" in user_input
        or "hi" in user_input
    ):

        return (
            "Greetings Tejas, "
            "how may I assist you?"
        )

    elif "how are you" in user_input:

        return (
            "Operating at full "
            "efficiency, Tejas."
        )

    elif (
        "thank you" in user_input
        or "thanks" in user_input
    ):

        return "Always at your service."

    elif "who are you" in user_input:

        return (
            "I am JARVIS, your "
            "personal intelligent assistant."
        )

    elif "good morning" in user_input:

        return (
            "Good morning Tejas. "
            "Ready when you are."
        )

    elif "good night" in user_input:

        return (
            "Good night Tejas. "
            "Entering low power mode."
        )

    elif "your name" in user_input:

        return "I am JARVIS."

    # --------------------------------
    # GEMINI AI
    # --------------------------------

    try:

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt,

            config=types.GenerateContentConfig(

                system_instruction="""
You are JARVIS, Tejas's personal futuristic AI assistant.

Rules:
- Never say you are Gemini.
- Never say you are Google AI.
- Your name is only JARVIS.
- Speak intelligently and confidently.
- Keep responses practical.
- Speak like a premium AI assistant.
- Short responses for casual questions.
- Detailed responses only when needed.
- Avoid overly robotic replies.
"""
            )
        )

        return response.text

    except Exception as e:

        print("AI ERROR:", e)

        return (
            "I am currently unable "
            "to access the AI servers."
        )