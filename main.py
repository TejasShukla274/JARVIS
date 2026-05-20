import threading

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