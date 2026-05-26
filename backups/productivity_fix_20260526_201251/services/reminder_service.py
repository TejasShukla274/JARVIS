import re
from datetime import datetime, timedelta

from database.reminders_db import (
    add_reminder,
    delete_matching_reminders,
    delete_reminder,
    list_upcoming,
    parse_datetime
)


DATETIME_PATTERNS = [
    "%Y-%m-%d %H:%M",
    "%d-%m-%Y %H:%M",
    "%d/%m/%Y %H:%M",
    "%I:%M %p",
    "%I %p",
    "%H:%M"
]


def parse_reminder_time(text):
    text = text.strip()

    relative_match = re.search(
        r"\bin\s+(\d+)\s*(minute|minutes|min|hour|hours|day|days)\b",
        text
    )

    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)

        if unit in {"minute", "minutes", "min"}:
            return datetime.now() + timedelta(minutes=amount)

        if unit in {"hour", "hours"}:
            return datetime.now() + timedelta(hours=amount)

        return datetime.now() + timedelta(days=amount)

    cleaned = (
        text.replace("today at", "")
        .replace("at", "")
        .strip()
    )

    for pattern in DATETIME_PATTERNS:
        try:
            parsed = datetime.strptime(cleaned, pattern)
        except ValueError:
            continue

        if pattern in {"%I:%M %p", "%I %p", "%H:%M"}:
            now = datetime.now()
            parsed = parsed.replace(
                year=now.year,
                month=now.month,
                day=now.day
            )

            if parsed < now:
                parsed += timedelta(days=1)

        return parsed

    return None


def extract_reminder_parts(command):
    text = command.lower().strip()

    if not (
        text.startswith("remind me to")
        or text.startswith("remind me")
        or text.startswith("set reminder")
        or text.startswith("create a reminder")
        or text.startswith("add reminder")
    ):
        return None

    cleaned = text
    cleaned = cleaned.replace("create a reminder", "", 1).strip()
    cleaned = cleaned.replace("add reminder", "", 1).strip()
    cleaned = cleaned.replace("set reminder", "", 1).strip()
    cleaned = cleaned.replace("remind me to", "", 1).strip()
    cleaned = cleaned.replace("remind me", "", 1).strip()

    splitters = [
        " in ",
        " at ",
        " on "
    ]

    for splitter in splitters:
        if splitter in cleaned:
            title, time_part = cleaned.split(splitter, 1)
            remind_at = parse_reminder_time(splitter.strip() + " " + time_part)

            if remind_at:
                return title.strip(), remind_at

    return None


def create_reminder_from_command(command):
    parts = extract_reminder_parts(command)

    if not parts:
        return (
            "I can set reminders like: "
            "remind me to call mom in 10 minutes."
        )

    title, remind_at = parts

    if not title:
        return "Please tell me what to remind you about."

    reminder_id = add_reminder(title, remind_at)

    return (
        f"Reminder {reminder_id} set for "
        f"{remind_at.strftime('%d %B %Y at %I:%M %p')}."
    )


def format_upcoming_reminders(limit=5):
    reminders = list_upcoming(limit=limit)

    if not reminders:
        return "You have no upcoming reminders."

    lines = []

    for reminder in reminders:
        remind_at = parse_datetime(reminder["remind_at"])
        lines.append(
            f"{reminder['id']}. {reminder['title']} "
            f"at {remind_at.strftime('%d %b %I:%M %p')}"
        )

    return "Upcoming reminders. " + " ".join(lines)


def delete_reminder_from_command(command):
    text = command.lower().strip()

    id_match = re.search(r"\breminder\s+(\d+)\b", text)

    if id_match:
        delete_reminder(int(id_match.group(1)))
        return f"Reminder {id_match.group(1)} deleted."

    cleaned = text
    cleaned = cleaned.replace("delete reminder", "", 1)
    cleaned = cleaned.replace("delete the reminder", "", 1)
    cleaned = cleaned.replace("remove reminder", "", 1)
    cleaned = cleaned.replace("remove the reminder", "", 1)
    cleaned = cleaned.replace("to ", "", 1).strip()

    if not cleaned:
        return "Which reminder should I delete?"

    deleted_count = delete_matching_reminders(cleaned)

    if deleted_count == 0:
        return "I could not find a matching reminder."

    if deleted_count == 1:
        return "Reminder deleted."

    return f"Deleted {deleted_count} matching reminders."
