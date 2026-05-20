# gui/audio_reactive.py

# handles live microphone volume detection
# used for orb animation reactivity

import sounddevice as sd
import numpy as np


# global volume variable
volume_level = 0


def audio_callback(indata, frames, time, status):

    global volume_level

    # calculate microphone loudness
    volume_norm = np.linalg.norm(indata) * 10

    # clamp value
    volume_level = min(volume_norm, 1.0)



def start_audio_listener():

    # starts background microphone stream

    stream = sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=44100
    )

    stream.start()

    return stream



def get_volume():

    # returns current microphone loudness

    return volume_level