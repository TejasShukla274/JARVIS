# core/memory_handler.py
#
# Orchestrates:  intent detection → MemoryManager → response generation.
# Includes a confirmation flow for overwriting existing memories.

from brain.memory_intent import detect_memory_intent
from memory.memory_manager import memory_manager

# ------------------------------------------------------------------
# Pending-confirmation state
# ------------------------------------------------------------------
# When Jarvis asks "Do you want me to update X?", the next user input
# is checked against this dict.  If the user confirms, the pending
# action is executed; otherwise it is discarded.

_pending = None   # None  or  {"action", "key", "old", "new", "category"}


def _pretty_key(key):
    """``home_city`` → ``home city``."""
    return key.replace("_", " ")


def _format_list(memories):
    """Build a spoken summary grouped by category."""
    if not memories:
        return "I don't have any saved information about you yet."

    by_cat = {}
    for m in memories:
        by_cat.setdefault(m["category"], []).append(m)

    lines = []
    for cat in sorted(by_cat):
        lines.append(f"{cat.title()}:")
        for m in by_cat[cat]:
            lines.append(f"  {_pretty_key(m['key'])}: {m['value']}")

    count = len(memories)
    header = f"I have {count} {'memory' if count == 1 else 'memories'} saved."
    return header + " " + " ".join(lines)


# ------------------------------------------------------------------
# Public entry point — called from command_handler.process_command()
# ------------------------------------------------------------------

def handle_memory_command(user_text):
    """Return a response string if *user_text* is a memory command,
    otherwise return ``None`` so the caller falls through to other handlers.
    """
    global _pending

    text = user_text.strip().lower()

    # ----------------------------------------------------------------
    # 1.  Check if we are waiting for a yes / no confirmation
    # ----------------------------------------------------------------
    if _pending is not None:
        if text in (
            "yes", "yeah", "yep", "sure", "confirm",
            "do it", "go ahead", "yes please", "ok", "okay",
            "affirmative", "absolutely", "of course",
        ):
            p = _pending
            _pending = None

            if p["action"] == "UPDATE":
                action, _ = memory_manager.save(p["key"], p["new"], p["category"])
                if action:
                    return (
                        f"Done. I've updated your {_pretty_key(p['key'])} "
                        f"from {p['old']} to {p['new']}."
                    )
                return "Sorry, something went wrong while updating. Please try again."

            if p["action"] == "DELETE":
                ok, old = memory_manager.delete(p["key"])
                if ok:
                    return f"Done. I've forgotten your {_pretty_key(p['key'])}."
                return "Sorry, I could not delete that memory."

        elif text in (
            "no", "nope", "cancel", "never mind",
            "don't", "forget it", "stop", "negative",
        ):
            _pending = None
            return "Alright, I won't make that change."

        else:
            # Not a yes/no — clear pending and continue with normal processing
            _pending = None

    # ----------------------------------------------------------------
    # 2.  Detect memory intent
    # ----------------------------------------------------------------
    intent = detect_memory_intent(user_text)

    if intent is None:
        return None   # not a memory command → fall through

    action = intent["intent"]
    key    = intent["key"]
    value  = intent["value"]
    cat    = intent["category"]

    print(f"MEMORY INTENT: {action}  key={key}  value={value}  category={cat}")

    # ----------------------------------------------------------------
    # 3.  Execute
    # ----------------------------------------------------------------

    # --- SAVE / UPDATE ---
    if action in ("SAVE", "UPDATE"):
        existing = memory_manager.get(key)

        # If the value already exists AND is different → ask for confirmation
        if existing and existing.lower() != (value or "").lower():
            _pending = {
                "action": "UPDATE",
                "key": key,
                "old": existing,
                "new": value,
                "category": cat,
            }
            return (
                f"Your {_pretty_key(key)} is currently set to {existing}. "
                f"Would you like me to update it to {value}?"
            )

        # Same value already stored
        if existing and existing.lower() == (value or "").lower():
            return f"I already know that. Your {_pretty_key(key)} is {existing}."

        # New memory — save directly
        result, _ = memory_manager.save(key, value, cat)
        if result:
            return f"Done. I've saved your {_pretty_key(key)} as {value}."
        return "Sorry, I couldn't save that right now. Please try again."

    # --- READ ---
    if action == "READ":
        value = memory_manager.get(key)
        if value:
            return f"Your {_pretty_key(key)} is {value}."
        return (
            f"I don't know your {_pretty_key(key)} yet. "
            f"You can tell me by saying 'my {_pretty_key(key)} is ...'."
        )

    # --- DELETE ---
    if action == "DELETE":
        if not memory_manager.exists(key):
            return f"I don't have any memory for {_pretty_key(key)}."

        old_value = memory_manager.get(key)
        _pending = {
            "action": "DELETE",
            "key": key,
            "old": old_value,
            "new": None,
            "category": cat,
        }
        return (
            f"Your {_pretty_key(key)} is currently {old_value}. "
            f"Are you sure you want me to forget it?"
        )

    # --- LIST ---
    if action == "LIST":
        memories = memory_manager.list_all(category=cat)
        return _format_list(memories)

    return None
