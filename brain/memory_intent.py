# brain/memory_intent.py
#
# Regex-based intent detection for memory commands.
# Runs BEFORE Gemini so common patterns are handled instantly (offline).
#
# Returns a dict like:
#   {"intent": "SAVE", "key": "name", "value": "Tejas", "category": "personal"}
# or None if the message is not a memory command.

import re

# ======================================================================
# Key aliases — maps natural phrases to canonical memory keys
# Sorted longest-first so multi-word keys match before single-word ones.
# ======================================================================

KEY_ALIASES = {
    "date of birth": "date_of_birth",
    "home city": "home_city",
    "home town": "home_city",
    "hometown": "home_city",
    "favorite game": "favorite_game",
    "favourite game": "favorite_game",
    "favorite car": "favorite_car",
    "favourite car": "favorite_car",
    "favorite color": "favorite_color",
    "favourite colour": "favorite_color",
    "favorite food": "favorite_food",
    "favourite food": "favorite_food",
    "favorite movie": "favorite_movie",
    "favourite movie": "favorite_movie",
    "favorite song": "favorite_song",
    "favourite song": "favorite_song",
    "favorite sport": "favorite_sport",
    "favourite sport": "favorite_sport",
    "favorite subject": "favorite_subject",
    "favourite subject": "favorite_subject",
    "phone number": "phone",
    "mobile number": "phone",
    "email id": "email",
    "email address": "email",
    "graduation year": "graduation_year",
    "nick name": "nickname",
    "github repo": "github_repo",
    "name": "name",
    "city": "home_city",
    "college": "college",
    "university": "college",
    "school": "school",
    "age": "age",
    "birthday": "birthday",
    "email": "email",
    "phone": "phone",
    "mobile": "phone",
    "branch": "branch",
    "nickname": "nickname",
    "github": "github",
    "instagram": "instagram",
    "twitter": "twitter",
    "creator": "creator",
    "workplace": "workplace",
    "company": "workplace",
    "job": "job",
    "roll number": "roll_number",
    "roll no": "roll_number",
}

# Build a regex alternation of known key phrases (longest first)
_KNOWN_KEYS_SORTED = sorted(KEY_ALIASES.keys(), key=len, reverse=True)
_KNOWN_KEYS_PATTERN = "|".join(re.escape(k) for k in _KNOWN_KEYS_SORTED)

# ======================================================================
# Category inference
# ======================================================================

CATEGORY_MAP = {
    "name": "personal",
    "age": "personal",
    "birthday": "personal",
    "date_of_birth": "personal",
    "home_city": "personal",
    "nickname": "personal",
    "email": "personal",
    "phone": "personal",
    "creator": "personal",
    "college": "education",
    "school": "education",
    "branch": "education",
    "graduation_year": "education",
    "roll_number": "education",
    "favorite_game": "preferences",
    "favorite_car": "preferences",
    "favorite_color": "preferences",
    "favorite_food": "preferences",
    "favorite_movie": "preferences",
    "favorite_song": "preferences",
    "favorite_sport": "preferences",
    "favorite_subject": "preferences",
    "github": "projects",
    "github_repo": "projects",
    "workplace": "work",
    "company": "work",
    "job": "work",
    "instagram": "contacts",
    "twitter": "contacts",
}


def _normalize_key(raw_key):
    """Convert a natural-language key phrase into a canonical snake_case key."""
    raw = raw_key.strip().lower()
    if raw in KEY_ALIASES:
        return KEY_ALIASES[raw]
    # Unknown key — just snake_case it
    return re.sub(r"\s+", "_", raw)


def _infer_category(key):
    return CATEGORY_MAP.get(key, "custom")


def _format_value(value):
    """Title-case values that look like proper nouns; leave numbers/URLs alone."""
    v = value.strip()
    if not v:
        return v
    # Don't touch numbers, emails, URLs, paths
    if v.isdigit() or "@" in v or "/" in v or "\\" in v:
        return v
    return v.title()


# ======================================================================
# Public API
# ======================================================================

def detect_memory_intent(user_text):
    """Analyse *user_text* and return a memory-intent dict, or ``None``.

    The returned dict has the shape::

        {
            "intent": "SAVE" | "UPDATE" | "READ" | "DELETE" | "LIST",
            "key":      str | None,
            "value":    str | None,
            "category": str | None,
        }
    """
    text = user_text.strip().lower()

    # Remove trailing punctuation for cleaner matching
    text = re.sub(r"[?\.\!]+$", "", text).strip()

    # ---- DELETE --------------------------------------------------
    m = re.match(r"^(?:forget|delete|remove|erase)\s+my\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        return {"intent": "DELETE", "key": key, "value": None, "category": _infer_category(key)}

    # ---- LIST (all) ----------------------------------------------
    if re.match(
        r"^(?:"
        r"what do you know about me|"
        r"show (?:me )?(?:my |all )?(?:saved )?(?:information|info|memories|data|profile)|"
        r"list (?:all )?(?:my )?memories|"
        r"show everything you know|"
        r"what all do you know|"
        r"what have you saved|"
        r"show my saved information"
        r")$",
        text,
    ):
        return {"intent": "LIST", "key": None, "value": None, "category": None}

    # ---- LIST by category ----------------------------------------
    m = re.match(
        r"^show\s+(personal|education|preferences|work|projects|contacts|custom)\s+"
        r"(?:memories|info|information|data)$",
        text,
    )
    if m:
        return {"intent": "LIST", "key": None, "value": None, "category": m.group(1)}

    # ---- READ ----------------------------------------------------
    # Fixed-key shortcuts
    if re.match(r"^who\s+am\s+i$", text):
        return {"intent": "READ", "key": "name", "value": None, "category": "personal"}

    if re.match(r"^where\s+do\s+i\s+live$", text):
        return {"intent": "READ", "key": "home_city", "value": None, "category": "personal"}

    # "what's my X" / "what is my X" / "whats my X"
    m = re.match(r"^what(?:'?s|\s+is)\s+my\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        return {"intent": "READ", "key": key, "value": None, "category": _infer_category(key)}

    # "do you know my X" / "do you remember my X"
    m = re.match(r"^do\s+you\s+(?:know|remember)\s+my\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        return {"intent": "READ", "key": key, "value": None, "category": _infer_category(key)}

    # "tell me my X"
    m = re.match(r"^tell\s+me\s+my\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        return {"intent": "READ", "key": key, "value": None, "category": _infer_category(key)}

    # ---- UPDATE (explicit) ----------------------------------------
    m = re.match(r"^(?:change|update)\s+my\s+(.+?)\s+to\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        value = _format_value(m.group(2))
        return {"intent": "UPDATE", "key": key, "value": value, "category": _infer_category(key)}

    # ---- SAVE (explicit) -----------------------------------------
    m = re.match(r"^set\s+my\s+(.+?)\s+(?:to|as)\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        value = _format_value(m.group(2))
        return {"intent": "SAVE", "key": key, "value": value, "category": _infer_category(key)}

    m = re.match(r"^remember\s+(?:that\s+)?my\s+(.+?)\s+is\s+(.+)$", text)
    if m:
        key = _normalize_key(m.group(1))
        value = _format_value(m.group(2))
        return {"intent": "SAVE", "key": key, "value": value, "category": _infer_category(key)}

    # ---- Conversational SAVE patterns ----------------------------

    # "my name is …"
    m = re.match(r"^my\s+name\s+is\s+(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "name", "value": value, "category": "personal"}

    # "call me …"
    m = re.match(r"^call\s+me\s+(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "nickname", "value": value, "category": "personal"}

    # "i live in …"
    m = re.match(r"^i\s+live\s+in\s+(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "home_city", "value": value, "category": "personal"}

    # "i am from …"
    m = re.match(r"^i\s+(?:am|come)\s+from\s+(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "home_city", "value": value, "category": "personal"}

    # "i study at/in …"
    m = re.match(r"^i\s+stud(?:y|ied)\s+(?:at|in)\s+(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "college", "value": value, "category": "education"}

    # "i work at/in/for …"
    m = re.match(r"^i\s+work\s+(?:at|in|for)\s+(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "workplace", "value": value, "category": "work"}

    # "i am N years old"
    m = re.match(r"^i\s+am\s+(\d+)\s+years?\s+old$", text)
    if m:
        return {"intent": "SAVE", "key": "age", "value": m.group(1), "category": "personal"}

    # "my birthday is …"  (already covered by the generic pattern below,
    # but adding explicitly for clarity)
    m = re.match(r"^my\s+birthday\s+is\s+(?:on\s+)?(.+)$", text)
    if m:
        value = _format_value(m.group(1))
        return {"intent": "SAVE", "key": "birthday", "value": value, "category": "personal"}

    # Generic "my <known-key> is <value>"
    m = re.match(
        rf"^my\s+({_KNOWN_KEYS_PATTERN})\s+is\s+(.+)$",
        text,
    )
    if m:
        key = _normalize_key(m.group(1))
        value = _format_value(m.group(2))
        return {"intent": "SAVE", "key": key, "value": value, "category": _infer_category(key)}

    # No memory intent detected
    return None
