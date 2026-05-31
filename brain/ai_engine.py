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


def _get_owner_name():
    """Fetch the owner's name from the memory system, if available."""
    try:
        from memory.owner_profile import get_owner_info
        name = get_owner_info("name")
        # Check if it's the fallback "I don't have that information" message
        if name and "don't have" not in name:
            return name
    except Exception:
        pass
    return None


def ask_jarvis(prompt):

    user_input = prompt.lower().strip()

    owner_name = _get_owner_name()
    greeting_name = f" {owner_name}" if owner_name else ""

    # --------------------------------
    # SIMPLE OFFLINE RESPONSES
    # --------------------------------

    if (
        "hello" in user_input
        or "hi" in user_input
    ):

        return (
            f"Greetings{greeting_name}, "
            "how may I assist you?"
        )

    elif "how are you" in user_input:

        return (
            "Operating at full "
            f"efficiency{greeting_name}."
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
            f"Good morning{greeting_name}. "
            "Ready when you are."
        )

    elif "good night" in user_input:

        return (
            f"Good night{greeting_name}. "
            "Entering low power mode."
        )

    elif "your name" in user_input:

        return "I am JARVIS."

    # --------------------------------
    # GEMINI AI
    # --------------------------------

    try:

        # Build a dynamic system instruction that includes known user info
        system_parts = [
            "You are JARVIS, a personal futuristic AI assistant.",
            "",
            "Rules:",
            "- Never say you are Gemini.",
            "- Never say you are Google AI.",
            "- Your name is only JARVIS.",
            "- Speak intelligently and confidently.",
            "- Keep responses practical.",
            "- Speak like a premium AI assistant.",
            "- Short responses for casual questions.",
            "- Detailed responses only when needed.",
            "- Avoid overly robotic replies.",
        ]

        if owner_name:
            system_parts.insert(1, f"Your owner's name is {owner_name}.")

        system_instruction = "\n".join(system_parts)

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=prompt,

            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        return response.text

    except Exception as e:

        print("AI ERROR:", e)

        return (
            "I am currently unable "
            "to access the AI servers."
        )