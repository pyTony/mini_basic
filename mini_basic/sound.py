"""BBC-style ``SOUND`` statement: basic tone (and noise) synthesis.

This is deliberately *not* a BBC sound-chip (SN76489) emulation. It maps the
four ``SOUND channel,amplitude,pitch,duration`` parameters onto a simple sine
wave (or, for the traditional noise channel 0, white noise) and plays it
through pygame's mixer:

- ``channel`` selects a pygame mixer channel (``channel MOD N``, where N is
  the number of available mixer channels), so overlapping ``SOUND`` calls on
  different channels do not cut each other off. Channel 0 (BBC's noise
  channel) plays white noise instead of a tone.
- ``amplitude`` 0 means "silent unless an envelope is active" on real
  hardware; since ``ENVELOPE`` is not implemented (see
  ``mini_basic/features/deferred.py``), amplitude 0 is silent here too.
  -1..-15 map linearly onto volume, -1 loudest.
- ``pitch`` 0-255 is mapped onto a frequency using the commonly cited
  reference point "pitch 53 is approximately middle C", with 48 pitch units
  per octave (4 units per semitone). This is an approximation, not the real
  chip's note table.
- ``duration`` is in the usual BBC units of 1/20s.

If pygame, numpy, or an actual audio device is unavailable (headless CI,
containers, etc.), every method here degrades to a silent no-op rather than
raising -- callers do not need to check availability first.
"""
from __future__ import annotations

import math
import random
import struct
from typing import Dict, Optional, Tuple

_SAMPLE_RATE = 22050
_MAX_SECONDS = 12.75  # BBC SOUND duration max: 255 * 0.05s.
_CACHE_LIMIT = 64
_MIDDLE_C_HZ = 261.6256
_PITCH_ANCHOR = 53.0
_UNITS_PER_OCTAVE = 48.0


def pitch_to_freq(pitch: float) -> float:
    """Approximate BBC SOUND pitch (0-255) -> frequency in Hz.

    Not chip-accurate: see module docstring.
    """
    return _MIDDLE_C_HZ * (2.0 ** ((pitch - _PITCH_ANCHOR) / _UNITS_PER_OCTAVE))


def amplitude_to_volume(amplitude: int) -> float:
    """BBC amplitude -15 (quiet) .. -1 (loud) -> 0..1 volume. 0 -> 0 (silent;
    real hardware uses amplitude 0 to mean "envelope controls volume", and
    ENVELOPE is not implemented)."""
    if amplitude == 0:
        return 0.0
    return max(1.0 / 15.0, min(1.0, (16 - abs(int(amplitude))) / 15.0))


class SoundEngine:
    """Lazily-initialised pygame mixer wrapper. Safe to use even when audio
    is unavailable -- every public method then becomes a no-op."""

    def __init__(self) -> None:
        self._pygame = None
        self._ready: Optional[bool] = None  # None = not yet attempted.
        self._num_channels = 8
        self._cache: Dict[Tuple[int, int, bool, int], object] = {}

    def _ensure_ready(self) -> bool:
        if self._ready is not None:
            return self._ready
        self._ready = False
        try:
            from .display import import_pygame
            pygame = import_pygame()
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self._pygame = pygame
            self._num_channels = max(8, pygame.mixer.get_num_channels())
            self._ready = True
        except Exception:
            self._ready = False
        return self._ready

    def _make_tone(self, freq: float, seconds: float, volume: float, noise: bool):
        pygame = self._pygame
        n = max(1, int(_SAMPLE_RATE * seconds))
        amp = max(0, min(32767, int(32767 * volume)))
        fade = max(0, min(n // 2, int(0.01 * _SAMPLE_RATE)))  # 10ms anti-click fade.
        try:
            import numpy as np  # type: ignore
            if noise:
                samples = np.random.randint(-amp, amp + 1, size=n, dtype=np.int16)
            else:
                t = np.arange(n, dtype=np.float64) / _SAMPLE_RATE
                wave = np.sin(2.0 * np.pi * freq * t)
                if fade > 0:
                    ramp = np.linspace(0.0, 1.0, fade)
                    wave[:fade] *= ramp
                    wave[-fade:] *= ramp[::-1]
                samples = (wave * amp).astype(np.int16)
            return pygame.sndarray.make_sound(samples)
        except Exception:
            # Pure-python fallback when numpy isn't installed (it's an
            # optional dependency -- see requirements-display.txt).
            buf = bytearray()
            for i in range(n):
                if noise:
                    v = float(random.randint(-amp, amp))
                else:
                    v = math.sin(2.0 * math.pi * freq * i / _SAMPLE_RATE) * amp
                    if fade and i < fade:
                        v *= i / fade
                    elif fade and i >= n - fade:
                        v *= (n - i) / fade
                buf += struct.pack('<h', int(v))
            return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, channel: int, amplitude: int, pitch: int, duration_units: int) -> None:
        """Play one BBC-style SOUND. Fire-and-forget: does not block."""
        if not self._ensure_ready():
            return
        seconds = max(0.0, min(_MAX_SECONDS, duration_units * 0.05))
        volume = amplitude_to_volume(amplitude)
        if seconds <= 0 or volume <= 0:
            return
        noise = (int(channel) % 4) == 0  # BBC channel 0 is the noise channel.
        freq = pitch_to_freq(max(0, min(255, int(pitch))))
        key = (round(freq), round(seconds * 20), noise, round(volume * 20))
        snd = self._cache.get(key)
        if snd is None:
            try:
                snd = self._make_tone(freq, seconds, volume, noise)
            except Exception:
                return
            if len(self._cache) >= _CACHE_LIMIT:
                self._cache.clear()
            self._cache[key] = snd
        try:
            idx = abs(int(channel)) % self._num_channels
            self._pygame.mixer.Channel(idx).play(snd)
        except Exception:
            try:
                snd.play()
            except Exception:
                pass


_engine: Optional[SoundEngine] = None


def get_sound_engine() -> SoundEngine:
    global _engine
    if _engine is None:
        _engine = SoundEngine()
    return _engine
