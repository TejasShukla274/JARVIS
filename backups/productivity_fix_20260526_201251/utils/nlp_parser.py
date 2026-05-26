# utils/nlp_parser.py

import re
from datetime import datetime, timedelta

def parse_relative_time(text):
    """
    Parses terms like:
    - 'in 5 minutes' / 'in 10 mins'
    - 'in 2 hours' / 'in an hour'
    - 'in 1 day' / 'in 3 days'
    
    Returns a datetime object if matched, else None.
    """
    text = text.lower().strip()
    
    # 1. Matches "in X minutes" or "in X mins" or "in a minute"
    min_match = re.search(r'\bin\s+(\d+|a|an)\s+(minute|minutes|min|mins)\b', text)
    if min_match:
        qty = min_match.group(1)
        minutes = 1 if qty in ('a', 'an') else int(qty)
        return datetime.now() + timedelta(minutes=minutes)
        
    # 2. Matches "in X hours" or "in X hrs" or "in an hour"
    hour_match = re.search(r'\bin\s+(\d+|a|an)\s+(hour|hours|hr|hrs)\b', text)
    if hour_match:
        qty = hour_match.group(1)
        hours = 1 if qty in ('a', 'an') else int(qty)
        return datetime.now() + timedelta(hours=hours)

    # 3. Matches "in X days" or "in a day"
    day_match = re.search(r'\bin\s+(\d+|a)\s+(day|days)\b', text)
    if day_match:
        qty = day_match.group(1)
        days = 1 if qty in ('a') else int(qty)
        return datetime.now() + timedelta(days=days)
        
    return None


def parse_time_component(text):
    """
    Extracts time strings like:
    - '7:30 pm' / '7:30pm'
    - '7 pm' / '7pm'
    - '19:30'
    - 'noon' / 'midnight'
    
    Returns (hour, minute) as tuple, or None.
    """
    text = (
        text.lower()
        .replace("a.m.", "am")
        .replace("p.m.", "pm")
        .replace("a. m.", "am")
        .replace("p. m.", "pm")
        .strip()
    )
    
    if "noon" in text:
        return 12, 0
    if "midnight" in text:
        return 0, 0
        
    # Pattern for HH:MM AM/PM or HH AM/PM
    time_ampm_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', text)
    if time_ampm_match:
        hour = int(time_ampm_match.group(1))
        minute = int(time_ampm_match.group(2)) if time_ampm_match.group(2) else 0
        meridian = time_ampm_match.group(3)
        
        if meridian == 'pm' and hour < 12:
            hour += 12
        elif meridian == 'am' and hour == 12:
            hour = 0
        return hour, minute

    # Pattern for HH:MM without AM/PM.
    time_24h_match = re.search(r'\b(\d{1,2}):(\d{2})\b', text)
    if time_24h_match:
        hour = int(time_24h_match.group(1))
        minute = int(time_24h_match.group(2))

        if hour <= 12:
            now = datetime.now()
            pm_candidate = hour + 12

            if now.hour >= 12 and pm_candidate < 24:
                hour = pm_candidate

        if 0 <= hour < 24 and 0 <= minute < 60:
            return hour, minute
            
    # Pattern for single digit hour (e.g. "at 7") without AM/PM
    at_digit_match = re.search(r'\bat\s+(\d{1,2})\b', text)
    if at_digit_match:
        hour = int(at_digit_match.group(1))
        # Default to future hour (if current hour is larger, assume PM/next day)
        current_hour = datetime.now().hour
        if hour < 12 and current_hour >= hour:
            # simple heuristic: if it is afternoon and they say "at 7", assume 7 PM
            if current_hour < 12 + hour:
                hour += 12
        return hour, 0
        
    return None


def parse_date_component(text):
    """
    Parses references to dates like:
    - 'today'
    - 'tomorrow'
    - 'day after tomorrow'
    - 'next monday' / 'on Friday'
    
    Returns a date object, or None.
    """
    text = text.lower().strip()
    today = datetime.now().date()
    
    if "day after tomorrow" in text:
        return today + timedelta(days=2)
    if "tomorrow" in text:
        return today + timedelta(days=1)
    if "today" in text:
        return today
        
    # Weekdays matching
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    
    for day_name, day_idx in weekdays.items():
        if day_name in text:
            current_day_idx = today.weekday()
            days_ahead = day_idx - current_day_idx
            if days_ahead <= 0: # Already passed or is today, assume next week's day
                days_ahead += 7
            
            # If they say "next friday" and friday is already next week, handles correctly
            if "next" in text:
                days_ahead += 7
                
            return today + timedelta(days=days_ahead)
            
    return today # Default to today if date is not specified but time is


def parse_reminder_nlp(text):
    """
    Extracts text to remind and target datetime from a conversational string.
    Example:
    'remind me to call the bank manager tomorrow at 4:30 PM'
    -> Returns ('call the bank manager', datetime_object)
    """
    orig_text = text
    text = text.lower().strip()
    
    # Remove wake trigger words
    clean_text = re.sub(r'^(jarvis\s*,?\s*|please\s*|could you\s*)', '', text)
    clean_text = re.sub(r'^(remind me to|create a reminder to|add a reminder to)\s+', '', clean_text)
    
    # 1. Check relative duration first (e.g. "in 2 hours")
    rel_dt = parse_relative_time(clean_text)
    if rel_dt:
        # Strip the matching "in X minutes/hours" part from the cleaner label
        label = re.sub(r'\bin\s+\d+\s+(minute|minutes|min|mins|hour|hours|hr|hrs|day|days)\b', '', clean_text)
        label = re.sub(r'\bin\s+(a|an)\s+(minute|hour|day)\b', '', label)
        return label.strip().capitalize(), rel_dt

    # 2. Else parse separate Time and Date components
    time_comp = parse_time_component(clean_text)
    date_comp = parse_date_component(clean_text)
    
    if time_comp:
        hour, minute = time_comp
        parsed_dt = datetime.combine(date_comp, datetime.min.time()).replace(hour=hour, minute=minute)
        
        # If the parsed time is in the past and date was assumed 'today', push to tomorrow
        if parsed_dt < datetime.now() and "today" not in clean_text and "tomorrow" not in clean_text:
            parsed_dt += timedelta(days=1)
            
        # Strip times/dates from description to get clean text
        # e.g., removes "tomorrow", "at 4:30 PM", "today", "on monday"
        label = clean_text
        label = re.sub(r'\b(today|tomorrow|day after tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next)\b', '', label)
        label = re.sub(r'\b(at\s+)?\d{1,2}(?::\d{2})?\s*(am|pm)?\b', '', label)
        label = re.sub(r'\bat\s+\d{1,2}\b', '', label)
        label = re.sub(r'\b(noon|midnight)\b', '', label)
        label = re.sub(r'\s{2,}', ' ', label) # Remove duplicate spacing
        
        return label.strip().capitalize(), parsed_dt
        
    # Fallback to 1 hour from now if no time component matches
    fallback_dt = datetime.now() + timedelta(hours=1)
    return clean_text.capitalize(), fallback_dt


def parse_alarm_nlp(text):
    """
    Parses a string like "set alarm for 7:30 am" or "set alarm at 18:00"
    Returns (HH:MM string, label)
    """
    text = (
        text.lower()
        .replace("a.m.", "am")
        .replace("p.m.", "pm")
        .replace("a. m.", "am")
        .replace("p. m.", "pm")
        .strip()
    )
    
    # Try to find time
    time_comp = parse_time_component(text)
    if time_comp:
        hour, minute = time_comp
        time_str = f"{hour:02d}:{minute:02d}"
        
        # Extract label (anything after "alarm for" or "alarm at" excluding time parts)
        label_match = re.search(r'(?:labeled|called|for|with label|note)\s+(.+)', text)
        label = label_match.group(1).strip() if label_match else "Alarm"
        # strip typical time patterns from label
        label = re.sub(r'\b\d{1,2}(?::\d{2})?\s*(am|pm)?\b', '', label).strip()
        
        return time_str, label.capitalize() or "Alarm"
        
    return None, None
