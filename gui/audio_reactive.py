# gui/audio_reactive.py

# handles live microphone volume detection
# used for orb animation reactivity

import threading

# global volume variable
volume_level = 0.0
_stream = None
_initialized = False

# Lazy-loaded modules
sd = None
np = None


def _lazy_init():
    global sd, np, _initialized
    if _initialized:
        return True
    try:
        # Import inside function to prevent blocking main thread imports
        import sounddevice as _sd
        import numpy as _np
        sd = _sd
        np = _np
        _initialized = True
        return True
    except Exception as e:
        print("JARVIS Audio Warning: Failed to import numpy/sounddevice packages:", e)
        return False


def audio_callback(indata, frames, time, status):
    global volume_level
    if np is None:
        return
    try:
        # calculate microphone loudness
        volume_norm = np.linalg.norm(indata) * 10
        # clamp value
        volume_level = min(volume_norm, 1.0)
    except Exception:
        volume_level = 0.0


def _bg_listener_start():
    global _stream
    if not _lazy_init():
        return
    try:
        # Initialize the audio stream (can block on systems with disconnected Bluetooth arrays)
        _stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=44100
        )
        _stream.start()
        print("JARVIS Audio listener started successfully.")
    except Exception as e:
        print("JARVIS Audio Warning: Could not start audio input stream (no input device or Bluetooth latency):", e)
        _stream = None


def start_audio_listener():
    # Starts background microphone stream in a separate thread so it NEVER blocks PyQt5 GUI startup
    t = threading.Thread(target=_bg_listener_start, daemon=True)
    t.start()
    return None


def get_volume():
    # returns current microphone loudness
    return volume_level