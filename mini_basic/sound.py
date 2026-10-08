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

``play_sample`` is the other half: it plays a real sample file (WAV, OGG,
...) via pygame's native loader, for ``*PLAY "file.wav"[,channel]`` -- for
cases where a synthesized tone isn't enough (e.g. a sampled sound effect).

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
    is unavailable -- every public method then becomes a no-op.

    The mixer may already be running under different settings than the
    ones this module would pick -- e.g. the display layer's
    ``pygame.init()`` (opened by a MODE statement before any SOUND runs)
    auto-initialises the mixer at 44100Hz/stereo. Buffers must be built to
    match whatever is actually active, not fixed constants, or
    ``sndarray.make_sound``/``mixer.Sound`` raises (channel-count or width
    mismatch) and the tone silently never plays.
    """

    def __init__(self) -> None:
        self._pygame = None
        self._ready: Optional[bool] = None  # None = not yet attempted.
        self._num_channels = 8
        self._rate = _SAMPLE_RATE
        self._bits = 16
        self._mixer_channels = 1
        self._cache: Dict[Tuple[int, int, bool, int], object] = {}
        self._sample_cache: Dict[str, object] = {}

    def _ensure_ready(self) -> bool:
        if self._ready is not None:
            return self._ready
        self._ready = False
        try:
            from .display import import_pygame
            pygame = import_pygame()
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1, buffer=512)
            rate, size, mixer_channels = pygame.mixer.get_init()
            self._rate = abs(rate)
            self._bits = abs(size)
            self._mixer_channels = abs(mixer_channels) if mixer_channels else 1
            self._pygame = pygame
            self._num_channels = max(8, pygame.mixer.get_num_channels())
            self._ready = True
        except Exception:
            self._ready = False
        return self._ready

    def _make_tone(self, freq: float, seconds: float, volume: float, noise: bool):
        pygame = self._pygame
        rate = self._rate
        n = max(1, int(rate * seconds))
        peak = (1 << (self._bits - 1)) - 1
        amp = max(0, min(peak, int(peak * volume)))
        fade = max(0, min(n // 2, int(0.01 * rate)))  # 10ms anti-click fade.
        dtype_name = {8: 'int8', 16: 'int16', 32: 'int32'}.get(self._bits, 'int16')
        pack_fmt = {8: '<b', 16: '<h', 32: '<i'}.get(self._bits, '<h')
        try:
            import numpy as np  # type: ignore
            if noise:
                mono = np.random.randint(-amp, amp + 1, size=n)
            else:
                t = np.arange(n, dtype=np.float64) / rate
                wave = np.sin(2.0 * np.pi * freq * t)
                if fade > 0:
                    ramp = np.linspace(0.0, 1.0, fade)
                    wave[:fade] *= ramp
                    wave[-fade:] *= ramp[::-1]
                mono = wave * amp
            mono = mono.astype(getattr(np, dtype_name))
            if self._mixer_channels >= 2:
                samples = np.repeat(mono.reshape(-1, 1), self._mixer_channels, axis=1)
            else:
                samples = mono
            return pygame.sndarray.make_sound(np.ascontiguousarray(samples))
        except Exception:
            # Pure-python fallback when numpy isn't installed (it's an
            # optional dependency -- see requirements-display.txt).
            buf = bytearray()
            for i in range(n):
                if noise:
                    v = float(random.randint(-amp, amp))
                else:
                    v = math.sin(2.0 * math.pi * freq * i / rate) * amp
                    if fade and i < fade:
                        v *= i / fade
                    elif fade and i >= n - fade:
                        v *= (n - i) / fade
                frame = struct.pack(pack_fmt, int(v))
                buf += frame * max(1, self._mixer_channels)
            return pygame.mixer.Sound(buffer=bytes(buf))

    def play_music(self, path: str, volume: float = 1.0, loop: bool = True) -> None:
        """Stream a (typically long) music file via pygame's ``mixer.music``
        rather than ``mixer.Sound``, so a multi-minute track isn't decoded
        into memory whole. Fire-and-forget, like the other methods here."""
        if not self._ensure_ready():
            return
        try:
            self._pygame.mixer.music.load(path)
            self._pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            self._pygame.mixer.music.play(-1 if loop else 0)
        except Exception:
            pass

    def stop_music(self) -> None:
        if self._pygame is None:
            return
        try:
            self._pygame.mixer.music.stop()
        except Exception:
            pass

    def play_sample(self, path: str, channel: Optional[int] = None) -> None:
        """Play a sound sample file (WAV, OGG, ...) via pygame's native
        loader. Fire-and-forget: does not block, and any failure (missing
        file, unsupported format, no audio device) is a silent no-op."""
        if not self._ensure_ready():
            return
        snd = self._sample_cache.get(path)
        if snd is None:
            try:
                snd = self._pygame.mixer.Sound(path)
            except Exception:
                return
            if len(self._sample_cache) >= _CACHE_LIMIT:
                self._sample_cache.clear()
            self._sample_cache[path] = snd
        try:
            if channel is None:
                snd.play()
            else:
                idx = abs(int(channel)) % self._num_channels
                self._pygame.mixer.Channel(idx).play(snd)
        except Exception:
            pass

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
