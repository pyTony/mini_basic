"""Floating-point platform facts and comparison helpers."""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass


def discover_machine_epsilon() -> float:
    """Return machine epsilon via the classic ``1 + eps`` loop.

    This is the same algorithm a BASIC program would use to *find* epsilon;
    the interpreter runs it once at startup and exposes the result as ``_epsilon``.
    """
    eps = 1.0
    while 1.0 + eps != 1.0:
        eps /= 2.0
    # Loop exits one halving past the last distinguishable value.
    return eps * 2.0


def machine_epsilon() -> float:
    """Platform float epsilon, cross-checked against the discovery loop."""
    discovered = discover_machine_epsilon()
    expected = sys.float_info.epsilon
    if discovered != expected:
        return expected
    return discovered


_IEEE754_BINARY64 = {
    'radix': 2,
    'mant_dig': 53,
    'dig': 15,
    'epsilon': 2.220446049250313e-16,
}


@dataclass(frozen=True)
class FloatPlatformInfo:
    """Read-only facts about the interpreter's ``float`` type."""

    epsilon: float
    decimal_digits: int
    mantissa_digits: int
    radix: int
    is_ieee754_binary64: bool
    max_value: float
    min_positive: float


def probe_float_platform() -> FloatPlatformInfo:
    """Gather float metadata for system variables and HELP text."""
    info = sys.float_info
    eps = machine_epsilon()
    is_ieee = (
        info.radix == _IEEE754_BINARY64['radix']
        and info.mant_dig == _IEEE754_BINARY64['mant_dig']
        and info.dig == _IEEE754_BINARY64['dig']
        and eps == _IEEE754_BINARY64['epsilon']
    )
    return FloatPlatformInfo(
        epsilon=eps,
        decimal_digits=info.dig,
        mantissa_digits=info.mant_dig,
        radix=info.radix,
        is_ieee754_binary64=is_ieee,
        max_value=info.max,
        min_positive=info.min,
    )


def near_equal(a: float, b: float, *, abs_tol: float | None = None) -> bool:
    """True when ``a`` and ``b`` are equal within machine-relative precision.

    With ``abs_tol``, uses that absolute tolerance instead (``NEAR(x,y,t)``).
    """
    if abs_tol is not None:
        return abs(a - b) <= abs_tol
    if a == b:
        return True
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= machine_epsilon() * scale


def near_equal_sig(a: float, b: float, sig_digits: int) -> bool:
    """True when ``a`` and ``b`` match to ``sig_digits`` significant figures."""
    n = int(sig_digits)
    if n < 1:
        return a == b
    if a == b:
        return True
    if a == 0.0 or b == 0.0:
        return abs(a - b) < 10.0 ** (-n)
    magnitude = math.floor(math.log10(abs(a)))
    scale = 10.0 ** (n - 1 - magnitude)
    return round(a * scale) == round(b * scale)


def basic_truth(value: bool) -> float:
    """MBASIC-style truth: -1 for true, 0 for false."""
    return -1.0 if value else 0.0


__all__ = [
    'FloatPlatformInfo',
    'basic_truth',
    'discover_machine_epsilon',
    'machine_epsilon',
    'near_equal',
    'near_equal_sig',
    'probe_float_platform',
]
