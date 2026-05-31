import threading
import sys

# 1. Initialize persistent memory FIRST to avoid C-extension/threading conflicts with PyQt5/speech_recognition on Windows
try:
    from database.mysql_connector import initialize_mysql
    from memory.memory_manager import memory_manager

    if initialize_mysql():
        memory_manager.initialize()
    else:
        print("WARNING: Memory system unavailable — MySQL is not running.", flush=True)
except Exception as e:
    print(f"WARNING: Memory initialization failed — {e}", flush=True)

# 2. Now import the rest of the application
from listener import wake_listener
from gui.main_window import launch_gui


if __name__ == "__main__":
    # START WAKE LISTENER IN BACKGROUND
    listener_thread = threading.Thread(
        target=wake_listener,
        daemon=True
    )
    listener_thread.start()

    # START GUI / ORB
    launch_gui()