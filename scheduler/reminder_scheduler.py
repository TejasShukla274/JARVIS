import threading
import time

from database.reminders_db import get_due_reminders, init_db, mark_triggered


class ReminderScheduler:

    def __init__(self, on_reminder, poll_seconds=15):
        self.on_reminder = on_reminder
        self.poll_seconds = poll_seconds
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True
        )

    def start(self):
        init_db()

        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        while not self._stop_event.is_set():
            due_reminders = get_due_reminders()

            for reminder in due_reminders:
                mark_triggered(reminder["id"])
                self.on_reminder(reminder)

            self._stop_event.wait(self.poll_seconds)
