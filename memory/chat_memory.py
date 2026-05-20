import json
import os

MEMORY_FILE = "memory/memory.json"


def load_memory(): #opens memory.json and loads old memory
    if not os.path.exists(MEMORY_FILE):
        return {"history": [], "user_data": {}}

    with open(MEMORY_FILE, "r") as file:
        return json.load(file)


def save_memory(data): #saves new data into memory
    with open(MEMORY_FILE, "w") as file:
        json.dump(data, file, indent=4)


def add_chat(user_message, jarvis_reply): #this stores conversation as pair i.e user and ai
    data = load_memory()

    data["history"].append({
        "user": user_message,
        "jarvis": jarvis_reply
    })

    if len(data["history"]) > 10:
        data["history"] = data["history"][-10:]

    save_memory(data)


def get_chat_history(): #brings the old messages so that ai can read it
    data = load_memory()
    history_text = ""

    for chat in data["history"]:
        history_text += f"User: {chat['user']}\nJARVIS: {chat['jarvis']}\n"

    return history_text


def save_user_data(key, value): #saves user data
    data = load_memory()
    data["user_data"][key] = value
    save_memory(data)


def get_user_data(): #gets the user data
    data = load_memory()
    return data["user_data"]