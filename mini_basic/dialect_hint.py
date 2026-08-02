"""Shebang and REM dialect hints embedded in .bas program sources."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .type_system import Dialect

_DIALECT_TOKEN = r'(mini|mits|bbc|commodore|tiny)'


@dataclass(frozen=True)
class DialectHint:
    dialect: Dialect
    strict: bool = False
    case_sensitive: Optional[bool] = None
    source: str = 'shebang'
    strip_line: bool = True


def _normalize_dialect_token(value: str) -> Optional[Dialect]:
    key = value.strip().lower()
    if key in ('mini', 'mits', 'bbc', 'commodore', 'tiny'):
        return key  # type: ignore[return-value]
    return None


def _modifiers_from_text(text: str) -> Tuple[bool, Optional[bool]]:
    lower = text.lower()
    strict = 'strict' in lower or '--strict-dialect' in lower
    case_sensitive: Optional[bool] = None
    if re.search(r'\b(case|sensitive)\b', lower):
        case_sensitive = True
    elif re.search(r'\b(fold|casefold|insensitive)\b', lower):
        case_sensitive = False
    return strict, case_sensitive


def parse_shebang_line(line: str) -> Optional[DialectHint]:
    stripped = line.strip()
    if not stripped.startswith('#!'):
        return None

    body = stripped[2:].strip()
    if not body:
        return None
    lower = body.lower()

    dialect: Optional[Dialect] = None
    direct = re.match(rf'^{_DIALECT_TOKEN}\b', lower)
    if direct:
        dialect = _normalize_dialect_token(direct.group(1))
    elif re.search(r'mini[_ -]?basic', lower):
        env_match = re.search(rf'--dialect[=\s]+{_DIALECT_TOKEN}', lower)
        if env_match:
            dialect = _normalize_dialect_token(env_match.group(1))
        else:
            colon_match = re.search(rf':\s*{_DIALECT_TOKEN}\b', lower)
            if colon_match:
                dialect = _normalize_dialect_token(colon_match.group(1))
            else:
                token_match = re.search(rf'\b{_DIALECT_TOKEN}\b', lower)
                if token_match:
                    dialect = _normalize_dialect_token(token_match.group(1))

    if dialect is None:
        return None

    strict, case_sensitive = _modifiers_from_text(lower)
    return DialectHint(
        dialect=dialect,
        strict=strict,
        case_sensitive=case_sensitive,
        source='shebang',
        strip_line=True,
    )


def _strip_leading_line_number(text: str) -> str:
    match = re.match(r'^\s*\d+\s+', text)
    if match:
        return text[match.end():]
    return text.strip()


def _comment_body_and_source(line: str) -> Optional[Tuple[str, str]]:
    """Return (body, source) for REM or apostrophe comment lines."""
    text = _strip_leading_line_number(line.strip())
    if text.upper().startswith('REM'):
        return text[3:].strip(), 'rem'
    if text.startswith("'"):
        return text[1:].strip(), 'apostrophe'
    return None


def parse_comment_dialect_line(line: str) -> Optional[DialectHint]:
    """Parse `REM dialect: bbc` or `' dialect: bbc` (BBC SAVE/EDIT style)."""
    parsed = _comment_body_and_source(line)
    if parsed is None:
        return None
    body, source = parsed
    lower = body.lower()

    explicit = re.match(
        rf'^(?:(?:mini[_ -]?basic)\s+)?dialect\s*[=:]\s*{_DIALECT_TOKEN}\b',
        lower,
    )
    if explicit:
        dialect = _normalize_dialect_token(explicit.group(1))
        strict, case_sensitive = _modifiers_from_text(lower)
        return DialectHint(
            dialect=dialect,
            strict=strict,
            case_sensitive=case_sensitive,
            source=source,
            strip_line=True,
        )

    paren = re.search(rf'\({_DIALECT_TOKEN}\s+dialect\)', lower)
    if paren:
        dialect = _normalize_dialect_token(paren.group(1))
        return DialectHint(
            dialect=dialect,
            strict=False,
            case_sensitive=None,
            source=source,
            strip_line=False,
        )

    return None


def parse_rem_dialect_line(line: str) -> Optional[DialectHint]:
    return parse_comment_dialect_line(line)


def split_dialect_hints(raw_lines: List[str]) -> Tuple[List[str], Optional[DialectHint]]:
    """Remove dialect hint lines from source and return the hint, if any."""
    lines = list(raw_lines)
    hint: Optional[DialectHint] = None

    while lines and not lines[0].strip():
        lines.pop(0)

    if lines:
        hint = parse_shebang_line(lines[0])
        if hint is not None:
            lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)

    if hint is None:
        while lines and not lines[0].strip():
            lines.pop(0)
        if lines:
            hint = parse_comment_dialect_line(lines[0])
            if hint is not None and hint.strip_line:
                lines.pop(0)
                while lines and not lines[0].strip():
                    lines.pop(0)

    return lines, hint
