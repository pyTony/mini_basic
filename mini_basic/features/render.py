"""Format feature matrix rows as plain text."""
from __future__ import annotations

from typing import Sequence

from .types import MatrixRow, TopicRow

_DIALECT_HEADER = f'{"Feature":<32} mits  com tiny  bbc  mini'


def format_dialect_matrix(rows: Sequence[MatrixRow]) -> str:
    lines = [
        '=== Dialect structure compatibility ===',
        '  mits=ELIZA  commodore=C64  tiny=1975  bbc=BETH  mini=superset',
        '',
        f'  {_DIALECT_HEADER}',
        f'  {"-" * 32} ----  --- ----  ---  ----',
    ]
    for feature, mits, com, tiny, bbc, mini in rows:
        lines.append(
            f'  {feature:<32} {mits:^4}  {com:^3} {tiny:^4}  {bbc:^3}  {mini:^4}'
        )
    lines.extend([
        '',
        '  + = yes   - = rejected in strict dialect   ~ = extension',
    ])
    return '\n'.join(lines)


def format_topic_matrix(
    title: str,
    rows: Sequence[TopicRow],
    *,
    spec_col: str = 'BB4W / dialect spec',
) -> str:
    lines = [
        f'=== {title} ===',
        f'  {"Feature":<28} {spec_col:<22} mini   tested  notes',
        f'  {"-" * 28} {"-" * 22} ----   ------  -----',
    ]
    for feature, spec, mini, tested, notes in rows:
        lines.append(
            f'  {feature:<28} {spec:<22} {mini:<4}   {tested:<6}  {notes}'
        )
    return '\n'.join(lines)


def format_deferred_matrix(rows: Sequence[tuple[str, str, str]]) -> str:
    lines = [
        '=== Deferred feature sets (intentionally not in scope yet) ===',
        '  Complete corpus + core BBC language first; revisit when stable.',
        '',
        f'  {"Area":<20} {"Feature":<32} reason',
        f'  {"-" * 20} {"-" * 32} ------',
    ]
    for area, feature, reason in rows:
        lines.append(f'  {area:<20} {feature:<32} {reason}')
    return '\n'.join(lines)
