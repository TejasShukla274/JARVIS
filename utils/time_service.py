# utils/time_service.py
# ─────────────────────────────────────────────────────────────────────────────
# Single source of truth for ALL time in JARVIS.
# Every clock, alarm, reminder, and timer MUST use these helpers.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime, timedelta, timezone


# ── Local helpers ────────────────────────────────────────────────────────────

def now_local():
    """Timezone-aware local datetime — used for display."""
    return datetime.now().astimezone()


def now_naive():
    """Naive local datetime — used for SQLite comparisons."""
    return datetime.now()


def iso_now():
    return now_naive().isoformat(timespec="seconds")


# ── Formatting ───────────────────────────────────────────────────────────────

def format_clock(value=None, with_seconds=True):
    value = value or now_local()
    return value.strftime("%I:%M:%S %p" if with_seconds else "%I:%M %p")


def format_date(value=None):
    value = value or now_local()
    return value.strftime("%A, %d %B %Y")


# ── World clocks ─────────────────────────────────────────────────────────────
# Pure offset-based — no pytz or zoneinfo dependency needed.
# Offsets are in hours from UTC.  DST is deliberately ignored for simplicity;
# the user can adjust offsets in the list below if needed.

WORLD_CLOCKS = [
    {"city": "Tokyo",    "offset_hours":  9.0,  "label": "JST"},
    {"city": "Moscow",   "offset_hours":  3.0,  "label": "MSK"},
    {"city": "New York", "offset_hours": -4.0,  "label": "EDT"},
    {"city": "London",   "offset_hours":  1.0,  "label": "BST"},
    {"city": "Sydney",   "offset_hours": 10.0,  "label": "AEST"},
    {"city": "Dubai",    "offset_hours":  4.0,  "label": "GST"},
]


def get_world_clocks():
    """
    Returns a list of dicts:
      [{"city": "Tokyo", "label": "JST", "time_str": "03:42 AM", "date_str": "27 May"}, ...]
    """
    utc_now = datetime.now(timezone.utc)
    results = []
    for entry in WORLD_CLOCKS:
        tz = timezone(timedelta(hours=entry["offset_hours"]))
        local_dt = utc_now.astimezone(tz)
        results.append({
            "city":     entry["city"],
            "label":    entry["label"],
            "time_str": local_dt.strftime("%I:%M %p"),
            "date_str": local_dt.strftime("%d %b"),
        })
    return results
