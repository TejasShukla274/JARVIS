# brain/memory.py
#
# Thin wrapper for backward compatibility.
# The real memory logic now lives in:
#   - brain/memory_intent.py   (intent detection)
#   - core/memory_handler.py   (orchestration)
#   - memory/memory_manager.py (CRUD)
#
# This file is kept so any old imports don't break.

from core.memory_handler import handle_memory_command


def remember_user_facts(user_message):
    """Legacy entry point — delegates to the new memory handler.

    Returns the response string if a memory intent was detected,
    or None otherwise.
    """
    return handle_memory_command(user_message)