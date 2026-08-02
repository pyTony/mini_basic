"""Load DEBUG_STEP.txt for status.html debugging section."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEBUG_STEP_PATH = _PROJECT_ROOT / 'DEBUG_STEP.txt'


def load_debug_step() -> Optional[Dict[str, str]]:
    """Parse DEBUG_STEP.txt key: value lines into a dict."""
    if not _DEBUG_STEP_PATH.is_file():
        return None
    data: Dict[str, str] = {}
    for raw in _DEBUG_STEP_PATH.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        data[key.strip().lower()] = value.strip()
    if not data.get('program') and not data.get('step'):
        return None
    return data