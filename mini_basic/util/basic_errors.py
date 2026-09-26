"""Turn Python exception text into BASIC error wording.

Expressions run through Python, so a bad BASIC expression can surface
messages like ``float() argument must be ... not 'complex'``. Programs and
users should see BASIC terms (syntax error, type mismatch, ...).
"""
from __future__ import annotations

import re

_LOCUS = re.compile(r'\s*\(<string>, line \d+\)')

# (pattern, BASIC wording) — first match wins; unmatched text is kept.
_RULES = (
    (re.compile(r"not 'complex'|math domain error|expected a (?:nonnegative|positive) input"),
     'illegal function call'),
    (re.compile(r'could not convert string to float|real number, not|'
                r'unsupported operand type|can only concatenate|'
                r"can't multiply sequence|bad operand type|"
                r"'\w+' object is not (?:callable|subscriptable)"),
     'type mismatch'),
    (re.compile(r'was never closed|unmatched|unexpected EOF|'
                r'is not (?:a container or )?iterable|unterminated string'),
     'syntax error'),
    (re.compile(r'(?:float |integer )?(?:division|modulo)(?: or modulo)? by zero'),
     'division by zero'),
    (re.compile(r'Result too large|math range error|int too large|'
                r'Numerical result out of range'),
     'overflow'),
)


def basic_error_wording(message: str) -> str:
    """Return *message* with Python-specific wording mapped to BASIC terms."""
    text = _LOCUS.sub('', message).strip()
    for pattern, wording in _RULES:
        if pattern.search(text):
            return wording
    return text


__all__ = ['basic_error_wording']
