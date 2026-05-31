# memory/owner_profile.py
#
# Dynamic owner profile — reads from the memory system.
# Starts empty on a fresh install. Jarvis learns everything
# through conversation and voice commands.

# In-memory cache populated at runtime by the memory system.
# Other modules can still call get_owner_info(key) without changes.
OWNER_DATA = {}


def get_owner_info(key):
    """Return the value for *key* from the owner profile.

    Returns a friendly fallback when the key has not been learned yet,
    so callers never crash on a fresh install.
    """
    lookup_key = "home_city" if key == "city" else key
    value = OWNER_DATA.get(lookup_key) or OWNER_DATA.get(key)

    if value:
        return value

    return "I don't have that information yet. You can tell me anytime."


def set_owner_info(key, value):
    """Store or update a single field in the runtime cache."""
    OWNER_DATA[key] = value


def load_owner_data_from_dict(data: dict):
    """Bulk-load a dict of key/value pairs into the runtime cache.

    Called once during startup after the memory system reads from the
    database so that modules using get_owner_info() work transparently.
    """
    OWNER_DATA.update(data)