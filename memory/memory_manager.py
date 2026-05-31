# memory/memory_manager.py
#
# Central memory service — the ONLY module that touches the memories table.
# All other Jarvis components interact with memory exclusively through this.

import threading


class MemoryManager:
    """Thread-safe CRUD service backed by MySQL with an in-memory cache."""

    def __init__(self):
        self._cache = {}          # {key: {"value": ..., "category": ...}}
        self._lock = threading.Lock()
        self._initialized = False

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def initialize(self):
        """Load every memory row from MySQL into the local cache.

        Called once from main.py after the MySQL pool is ready.
        """
        try:
            from database.mysql_connector import get_mysql_connection, is_available

            if not is_available():
                print("MEMORY: MySQL not available — skipping cache load.")
                return

            with get_mysql_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT memory_key, memory_value, category "
                    "FROM memories WHERE user_id = 'default'"
                )
                rows = cursor.fetchall()

            with self._lock:
                for row in rows:
                    self._cache[row["memory_key"]] = {
                        "value": row["memory_value"],
                        "category": row["category"],
                    }

            self._initialized = True
            self._sync_to_owner_profile()
            print(f"MEMORY: Loaded {len(rows)} memories from MySQL.")

        except Exception as e:
            print(f"MEMORY INIT ERROR: {e}")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, key, value, category="personal"):
        """Insert or update a memory.  Returns ``(action, old_value)``."""
        old_value = self.get(key)
        try:
            from database.mysql_connector import get_mysql_connection

            with get_mysql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memories (memory_key, memory_value, category) "
                    "VALUES (%s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE memory_value = %s, category = %s",
                    (key, value, category, value, category),
                )

            with self._lock:
                self._cache[key] = {"value": value, "category": category}

            action = "UPDATE" if old_value else "CREATE"
            self._log(action, key, old_value, value)
            self._sync_to_owner_profile()

            print(f"MEMORY SAVED: {key} = {value}  [category={category}]")
            return action, old_value

        except Exception as e:
            print(f"MEMORY SAVE ERROR: {e}")
            return None, None

    def get(self, key):
        """Return the value for *key*, or ``None``."""
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                print(f"MEMORY FOUND: {key} = {entry['value']}")
                return entry["value"]
        print(f"MEMORY NOT FOUND: {key}")
        return None

    def delete(self, key):
        """Delete a memory.  Returns ``(success, old_value)``."""
        old_value = self.get(key)
        if old_value is None:
            return False, None

        try:
            from database.mysql_connector import get_mysql_connection

            with get_mysql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM memories "
                    "WHERE memory_key = %s AND user_id = 'default'",
                    (key,),
                )

            with self._lock:
                self._cache.pop(key, None)

            self._log("DELETE", key, old_value=old_value)
            self._sync_to_owner_profile()

            print(f"MEMORY DELETED: {key}  (was: {old_value})")
            return True, old_value

        except Exception as e:
            print(f"MEMORY DELETE ERROR: {e}")
            return False, None

    def exists(self, key):
        with self._lock:
            return key in self._cache

    # ------------------------------------------------------------------
    # Search / List
    # ------------------------------------------------------------------

    def search(self, query):
        """Return memories whose key or value contain *query*."""
        query_lower = query.lower()
        results = []
        with self._lock:
            for key, entry in self._cache.items():
                if query_lower in key.lower() or query_lower in entry["value"].lower():
                    results.append({
                        "key": key,
                        "value": entry["value"],
                        "category": entry["category"],
                    })
        return results

    def list_all(self, category=None):
        """Return all memories, optionally filtered by *category*."""
        results = []
        with self._lock:
            for key, entry in self._cache.items():
                if category and entry["category"] != category:
                    continue
                results.append({
                    "key": key,
                    "value": entry["value"],
                    "category": entry["category"],
                })
        return results

    def get_categories(self):
        """Return the set of distinct categories currently stored."""
        with self._lock:
            return list({e["category"] for e in self._cache.values()})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, action, key, old_value=None, new_value=None):
        """Write an audit row to memory_logs."""
        try:
            from database.mysql_connector import get_mysql_connection

            with get_mysql_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memory_logs "
                    "(action, memory_key, old_value, new_value) "
                    "VALUES (%s, %s, %s, %s)",
                    (action, key, old_value, new_value),
                )
        except Exception as e:
            print(f"MEMORY LOG ERROR: {e}")

    def _sync_to_owner_profile(self):
        """Push cached data into ``owner_profile.OWNER_DATA`` for backward
        compatibility with modules that still call ``get_owner_info()``."""
        try:
            from memory.owner_profile import load_owner_data_from_dict

            with self._lock:
                data = {k: v["value"] for k, v in self._cache.items()}
            load_owner_data_from_dict(data)
        except Exception as e:
            print(f"MEMORY SYNC ERROR: {e}")


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------
memory_manager = MemoryManager()
