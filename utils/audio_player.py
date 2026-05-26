# utils/audio_player.py
# ─────────────────────────────────────────────────────────────────────────────
# Fully offline audio system for JARVIS.
# Generates alarm WAV tones programmatically — no external sound files needed.
# Uses winsound.PlaySound (WAV) as primary, winsound.Beep as fallback.
# ─────────────────────────────────────────────────────────────────────────────

import io
import math
import os
import struct
import sys
import tempfile
import threading
import time
import wave

if sys.platform == "win32":
    import winsound
else:
    winsound = None

from voice.voice_output import speak


# ── Generated alarm WAV cache ────────────────────────────────────────────────
_alarm_wav_path = None
_notification_wav_path = None


def _generate_sine_wav(filename, frequency=880, duration_ms=600,
                       sample_rate=22050, volume=0.7):
    """Creates a small WAV file with a sine-wave tone."""
    n_samples = int(sample_rate * duration_ms / 1000)
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            value = volume * math.sin(2 * math.pi * frequency * t)
            # Apply fade-in (first 5%) and fade-out (last 5%)
            fade_samples = int(n_samples * 0.05)
            if i < fade_samples:
                value *= i / fade_samples
            elif i > n_samples - fade_samples:
                value *= (n_samples - i) / fade_samples
            sample = int(value * 32767)
            wf.writeframes(struct.pack("<h", sample))


def _generate_alarm_wav(filename, sample_rate=22050, volume=0.75):
    """Creates a pulsing two-tone alarm WAV (about 2 seconds)."""
    total_ms = 2000
    n_samples = int(sample_rate * total_ms / 1000)
    frames = []
    for i in range(n_samples):
        t = i / sample_rate
        # Alternate between high and low tone every 250ms
        cycle = int(t * 4) % 2
        freq = 1400 if cycle == 0 else 900
        # Add slight vibrato
        freq += 30 * math.sin(2 * math.pi * 6 * t)
        value = volume * math.sin(2 * math.pi * freq * t)
        # Pulse envelope
        pulse_t = (t * 4) % 1.0
        envelope = 1.0 - 0.3 * pulse_t
        value *= envelope
        # Fade in first 3%
        fade_in = int(n_samples * 0.03)
        if i < fade_in:
            value *= i / fade_in
        sample = max(-32767, min(32767, int(value * 32767)))
        frames.append(struct.pack("<h", sample))

    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))


def _ensure_generated_wavs():
    """Lazily generate alarm/notification WAV files on first use."""
    global _alarm_wav_path, _notification_wav_path

    cache_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets"
    )
    os.makedirs(cache_dir, exist_ok=True)

    alarm_path = os.path.join(cache_dir, "_jarvis_alarm.wav")
    notif_path = os.path.join(cache_dir, "_jarvis_notif.wav")

    if not os.path.exists(alarm_path):
        try:
            _generate_alarm_wav(alarm_path)
        except Exception as e:
            print(f"WAV generation error (alarm): {e}")
            alarm_path = None

    if not os.path.exists(notif_path):
        try:
            _generate_sine_wav(notif_path, frequency=2200, duration_ms=120,
                               volume=0.5)
        except Exception as e:
            print(f"WAV generation error (notif): {e}")
            notif_path = None

    _alarm_wav_path = alarm_path
    _notification_wav_path = notif_path


# ── AlarmSoundHandle ─────────────────────────────────────────────────────────

class AlarmSoundHandle:
    def __init__(self, stop_event, thread=None):
        self.stop_event = stop_event
        self.thread = thread

    def stop(self):
        self.stop_event.set()
        if winsound:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass


# ── Beep fallback ────────────────────────────────────────────────────────────

def play_electronic_beep(frequency=1500, duration=150):
    """Windows Beep fallback — works offline with zero dependency."""
    if winsound:
        try:
            winsound.Beep(frequency, duration)
        except Exception:
            pass


# ── Notification beep ────────────────────────────────────────────────────────

def play_notification_beep():
    """Double-tone success notification."""
    def _play():
        _ensure_generated_wavs()
        if winsound and _notification_wav_path and os.path.exists(_notification_wav_path):
            try:
                winsound.PlaySound(
                    _notification_wav_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
                return
            except Exception:
                pass
        # Fallback
        play_electronic_beep(2000, 80)
        time.sleep(0.05)
        play_electronic_beep(2500, 120)

    threading.Thread(target=_play, daemon=True).start()


# ── Alarm loop (continuous until stopped) ────────────────────────────────────

def play_alarm_loop_async(custom_sound=None, volume=85, fade_in=True,
                          stop_event=None):
    """
    Starts an offline alarm loop.
    Priority order:
      1. Custom WAV file (if provided and exists)
      2. Generated JARVIS alarm WAV (reliable on all Windows)
      3. winsound.Beep synthetic tones (fallback)
    """
    stop_event = stop_event or threading.Event()
    volume = max(0, min(100, int(volume)))

    _ensure_generated_wavs()

    # Determine which WAV to use
    wav_to_play = None
    if custom_sound and os.path.exists(custom_sound) and custom_sound.lower().endswith(".wav"):
        wav_to_play = custom_sound
    elif _alarm_wav_path and os.path.exists(_alarm_wav_path):
        wav_to_play = _alarm_wav_path

    if winsound and wav_to_play:
        def wav_loop():
            try:
                # Loop the WAV
                winsound.PlaySound(
                    wav_to_play,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                )
                # Keep running until stopped
                while not stop_event.is_set():
                    time.sleep(0.1)
            finally:
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except Exception:
                    pass

        thread = threading.Thread(target=wav_loop, daemon=True)
        thread.start()
        return AlarmSoundHandle(stop_event, thread)

    # Fallback: synthetic Beep loop
    def synth_loop():
        start = time.monotonic()
        while not stop_event.is_set():
            elapsed = time.monotonic() - start
            fade_ratio = min(1.0, elapsed / 6.0) if fade_in else 1.0
            intensity = max(0.2, (volume / 100.0) * fade_ratio)
            high = int(1200 + 700 * intensity)
            low = int(800 + 400 * intensity)
            pulse = int(80 + 80 * intensity)

            play_electronic_beep(high, pulse)
            if stop_event.wait(0.06):
                break
            play_electronic_beep(low, pulse)
            if stop_event.wait(max(0.1, 0.3 - 0.1 * intensity)):
                break

    thread = threading.Thread(target=synth_loop, daemon=True)
    thread.start()
    return AlarmSoundHandle(stop_event, thread)


# ── Voice alert wrapper ──────────────────────────────────────────────────────

def speak_alert(message):
    """Speaks an alert message using JARVIS's offline TTS system."""
    speak(message)
