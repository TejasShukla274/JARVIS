# database/db_manager.py

import sqlite3
import os
import json
from pathlib import Path
from contextlib import contextmanager

DB_DIR = Path(__file__).resolve().parents[1] / "database"
DB_FILE = DB_DIR / "jarvis_productivity.db"

# Ensure the database directory exists
os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db_connection():
    """
    Context manager to handle open/close connection cycles cleanly.
    Ensures safe operations across multiple background thread calls.
    """
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def initialize_database():
    """
    Initializes all the required SQLite tables with the specified relational schema.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. ALARMS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,          -- Format 'HH:MM' (24-hour)
                label TEXT,                  -- Optional note/label
                repeat_days TEXT,            -- JSON list of active days: [0,1,2,3,4,5,6] (0 = Mon, 6 = Sun)
                is_active INTEGER DEFAULT 1, -- Boolean flag (0 or 1)
                snooze_count INTEGER DEFAULT 0,
                custom_sound TEXT            -- Path to a local WAV/MP3 sound file
            )
        """)

        # 2. REMINDERS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,          -- What to remind
                datetime TEXT NOT NULL,      -- ISO-8601 string 'YYYY-MM-DD HH:MM:SS'
                category TEXT DEFAULT 'General',
                priority TEXT DEFAULT 'Medium', -- 'Low', 'Medium', 'High'
                recurrence TEXT DEFAULT 'None', -- 'None', 'Daily', 'Weekly', 'Monthly'
                is_completed INTEGER DEFAULT 0
            )
        """)

        # 3. TASKS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                due_date TEXT,               -- ISO Date 'YYYY-MM-DD' or DateTime
                priority TEXT DEFAULT 'Medium', -- 'Low', 'Medium', 'High'
                tags TEXT DEFAULT '[]',       -- JSON list of strings
                category TEXT DEFAULT 'Work',
                status TEXT DEFAULT 'todo',   -- 'todo', 'doing', 'done'
                is_completed INTEGER DEFAULT 0
            )
        """)

        # 4. EVENTS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                start_time TEXT NOT NULL,    -- ISO format 'YYYY-MM-DD HH:MM:SS'
                end_time TEXT NOT NULL,      -- ISO format 'YYYY-MM-DD HH:MM:SS'
                color TEXT DEFAULT '#00aaff', -- Neon blue hex color
                category TEXT DEFAULT 'Meeting'
            )
        """)

        # 5. TIMER LOGS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                duration_seconds INTEGER NOT NULL,
                completed_at TEXT NOT NULL,  -- ISO format datetime
                label TEXT DEFAULT 'Timer'
            )
        """)

        # 6. SETTINGS TABLE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Seed default settings if empty
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            default_settings = [
                ("theme", "futuristic-dark"),
                ("pomodoro_duration", "25"),
                ("short_break", "5"),
                ("long_break", "15"),
                ("sound_enabled", "1"),
                ("startup_launch", "0")
            ]
            cursor.executemany("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", default_settings)


# Initialize schema immediately on import
initialize_database()

# =====================================================================
# DATABASE CRUD UTILITIES
# =====================================================================

# --- ALARMS ---

def add_alarm(time, label="", repeat_days="[]", is_active=1, custom_sound=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alarms (time, label, repeat_days, is_active, snooze_count, custom_sound) VALUES (?, ?, ?, ?, 0, ?)",
            (time, label, repeat_days, is_active, custom_sound)
        )
        return cursor.lastrowid

def get_alarms():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alarms ORDER BY time ASC")
        return [dict(row) for row in cursor.fetchall()]

def update_alarm(alarm_id, time=None, label=None, repeat_days=None, is_active=None, custom_sound=None):
    fields = []
    values = []
    if time is not None:
        fields.append("time = ?")
        values.append(time)
    if label is not None:
        fields.append("label = ?")
        values.append(label)
    if repeat_days is not None:
        fields.append("repeat_days = ?")
        values.append(repeat_days)
    if is_active is not None:
        fields.append("is_active = ?")
        values.append(int(is_active))
    if custom_sound is not None:
        fields.append("custom_sound = ?")
        values.append(custom_sound)
    
    if not fields:
        return False
        
    values.append(alarm_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE alarms SET {', '.join(fields)} WHERE id = ?", tuple(values))
        return cursor.rowcount > 0

def delete_alarm(alarm_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
        return cursor.rowcount > 0

# --- REMINDERS ---

def add_reminder(text, datetime_str, category="General", priority="Medium", recurrence="None"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (text, datetime, category, priority, recurrence, is_completed) VALUES (?, ?, ?, ?, ?, 0)",
            (text, datetime_str, category, priority, recurrence)
        )
        return cursor.lastrowid

def get_reminders(include_completed=False):
    query = "SELECT * FROM reminders" if include_completed else "SELECT * FROM reminders WHERE is_completed = 0"
    query += " ORDER BY datetime ASC"
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]

def update_reminder(reminder_id, text=None, datetime_str=None, category=None, priority=None, recurrence=None, is_completed=None):
    fields = []
    values = []
    if text is not None:
        fields.append("text = ?")
        values.append(text)
    if datetime_str is not None:
        fields.append("datetime = ?")
        values.append(datetime_str)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if priority is not None:
        fields.append("priority = ?")
        values.append(priority)
    if recurrence is not None:
        fields.append("recurrence = ?")
        values.append(recurrence)
    if is_completed is not None:
        fields.append("is_completed = ?")
        values.append(int(is_completed))
        
    if not fields:
        return False
        
    values.append(reminder_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE reminders SET {', '.join(fields)} WHERE id = ?", tuple(values))
        return cursor.rowcount > 0

def delete_reminder(reminder_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        return cursor.rowcount > 0

# --- TASKS ---

def add_task(title, description="", due_date=None, priority="Medium", tags="[]", category="Work", status="todo"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, due_date, priority, tags, category, status, is_completed) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (title, description, due_date, priority, tags, category, status)
        )
        return cursor.lastrowid

def get_tasks(status=None):
    query = "SELECT * FROM tasks"
    params = []
    if status is not None:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY id DESC"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

def update_task(task_id, title=None, description=None, due_date=None, priority=None, tags=None, category=None, status=None, is_completed=None):
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if due_date is not None:
        fields.append("due_date = ?")
        values.append(due_date)
    if priority is not None:
        fields.append("priority = ?")
        values.append(priority)
    if tags is not None:
        fields.append("tags = ?")
        values.append(tags)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
    if status is not None:
        fields.append("status = ?")
        values.append(status)
        if status.lower() == "done":
            fields.append("is_completed = ?")
            values.append(1)
        else:
            fields.append("is_completed = ?")
            values.append(0)
    if is_completed is not None:
        fields.append("is_completed = ?")
        values.append(int(is_completed))
        
    if not fields:
        return False
        
    values.append(task_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", tuple(values))
        return cursor.rowcount > 0

def delete_task(task_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0

# --- EVENTS ---

def add_event(title, description, start_time, end_time, color="#00aaff", category="Meeting"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (title, description, start_time, end_time, color, category) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, start_time, end_time, color, category)
        )
        return cursor.lastrowid

def get_events():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events ORDER BY start_time ASC")
        return [dict(row) for row in cursor.fetchall()]

def update_event(event_id, title=None, description=None, start_time=None, end_time=None, color=None, category=None):
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if start_time is not None:
        fields.append("start_time = ?")
        values.append(start_time)
    if end_time is not None:
        fields.append("end_time = ?")
        values.append(end_time)
    if color is not None:
        fields.append("color = ?")
        values.append(color)
    if category is not None:
        fields.append("category = ?")
        values.append(category)
        
    if not fields:
        return False
        
    values.append(event_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE events SET {', '.join(fields)} WHERE id = ?", tuple(values))
        return cursor.rowcount > 0

def delete_event(event_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return cursor.rowcount > 0

# --- TIMER LOGS ---

def add_timer_log(duration_seconds, completed_at, label="Timer"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO timer_logs (duration_seconds, completed_at, label) VALUES (?, ?, ?)",
            (duration_seconds, completed_at, label)
        )
        return cursor.lastrowid

def get_timer_logs():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timer_logs ORDER BY completed_at DESC")
        return [dict(row) for row in cursor.fetchall()]

# --- SETTINGS ---

def get_setting(key, default=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

def set_setting(key, value):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
