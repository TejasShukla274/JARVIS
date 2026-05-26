import re
from datetime import datetime

from database.db_manager import add_reminder, delete_reminder, get_reminders
from database.db_manager import delete_reminder as delete_productivity_reminder
from utils.nlp_parser import parse_reminder_nlp


def create_reminder_from_command(command):
    title, remind_at = parse_reminder_nlp(command)

    if not title:
        return "Please tell me what to remind you about."

    reminder_id = add_reminder(
        text=title,
        datetime_str=remind_at.isoformat(timespec="seconds"),
        category="Voice",
        priority="Medium",
        recurrence="None"
    )

    return (
        f"Reminder {reminder_id} set for "
        f"{remind_at.strftime('%d %B %Y at %I:%M %p')}."
    )


def format_upcoming_reminders(limit=5):
    reminders = get_reminders(include_completed=False)[:limit]

    if not reminders:
        return "You have no upcoming reminders."

    lines = []

    for reminder in reminders:
        remind_at = datetime.fromisoformat(reminder["datetime"])
        lines.append(
            f"{reminder['id']}. {reminder['text']} "
            f"at {remind_at.strftime('%d %b %I:%M %p')}"
        )

    return "Upcoming reminders. " + " ".join(lines)


def delete_reminder_from_command(command):
    text = command.lower().strip()

    id_match = re.search(r"\breminder\s+(\d+)\b", text)

    if id_match:
        delete_productivity_reminder(int(id_match.group(1)))
        return f"Reminder {id_match.group(1)} deleted."

    cleaned = text
    cleaned = cleaned.replace("delete reminder", "", 1)
    cleaned = cleaned.replace("delete the reminder", "", 1)
    cleaned = cleaned.replace("remove reminder", "", 1)
    cleaned = cleaned.replace("remove the reminder", "", 1)
    cleaned = cleaned.replace("to ", "", 1).strip()

    if not cleaned:
        return "Which reminder should I delete?"

    deleted_count = 0
    for reminder in get_reminders(include_completed=False):
        if cleaned in reminder["text"].lower():
            delete_reminder(reminder["id"])
            deleted_count += 1

    if deleted_count == 0:
        return "I could not find a matching reminder."

    if deleted_count == 1:
        return "Reminder deleted."

    return f"Deleted {deleted_count} matching reminders."
