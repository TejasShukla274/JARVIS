import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "reminders.db"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT,
                remind_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reminders_due
            ON reminders(status, remind_at)
            """
        )


def format_datetime(value):
    return value.strftime(DATETIME_FORMAT)


def parse_datetime(value):
    return datetime.strptime(value, DATETIME_FORMAT)


def add_reminder(title, remind_at, message=""):
    init_db()

    now_text = format_datetime(datetime.now())

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reminders (title, message, remind_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                title.strip(),
                message.strip(),
                format_datetime(remind_at),
                now_text
            )
        )

        return cursor.lastrowid


def list_upcoming(limit=25):
    init_db()

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, title, message, remind_at, status, created_at
            FROM reminders
            WHERE status = 'pending'
            ORDER BY remind_at ASC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return [dict(row) for row in rows]


def get_due_reminders(now=None):
    init_db()

    now = now or datetime.now()

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, title, message, remind_at, status, created_at
            FROM reminders
            WHERE status = 'pending'
              AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (format_datetime(now),)
        ).fetchall()

    return [dict(row) for row in rows]


def mark_triggered(reminder_id):
    init_db()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reminders
            SET status = 'triggered'
            WHERE id = ?
            """,
            (reminder_id,)
        )


def delete_reminder(reminder_id):
    init_db()

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM reminders
            WHERE id = ?
            """,
            (reminder_id,)
        )


def delete_matching_reminders(query):
    init_db()

    query = query.strip().lower()

    if not query:
        return 0

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM reminders
            WHERE status = 'pending'
              AND LOWER(title) LIKE ?
            """,
            (f"%{query}%",)
        )

        return cursor.rowcount
