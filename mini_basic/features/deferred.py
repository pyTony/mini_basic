"""Features explicitly out of scope until core corpus/language work is done."""
from __future__ import annotations

from typing import List

from .types import DeferredRow

DEFERRED_ROWS: List[DeferredRow] = [
    ('RISC OS WIMP', 'MENU / ATTACH / DETACH', 'desktop GUI toolkit'),
    ('RISC OS WIMP', 'ICON / WINDOW / WIMP_*', 'sprite icons and window ops'),
    ('RISC OS WIMP', 'MOUSE click handlers ON MOUSE', 'event-driven UI'),
    ('Inline ASM', 'OSASM / [ / ] assembler', 'ARM/x86 inline assembly'),
    ('Inline ASM', 'CALL / USR machine code', 'register ABI and memory model'),
    ('Inline ASM', 'OPT FN / assembler labels', 'low-level linking'),
    ('OS integration', 'SYS Windows API calls', 'foreign function interface'),
    ('OS integration', 'INSTALL libraries', 'tokenised library load'),
    ('Structures', 'DIM struct{} / TYPE', 'user-defined record types'),
    (
        'Structures',
        'struct-array element read (tags)',
        'circle{(I%)}.r% read fails; write circle{(0)}.r%=v is silently '
        'tolerated. RETURN struct from FN. See examples/graphics/surks.bbc',
    ),
    ('Pointers', '? ! $ $$ indirection', 'byte/word/string pointers'),
    (
        'Sound',
        'Real SOUND / ENVELOPE / ADVAL audio',
        'multi-channel synthesis; stubs today: ENVELOPE no-op, SOUND silent+wait',
    ),
    # MODE 7 teletext: double-height + conceal implemented; boxed / full SAA5050 deferred.
    ('Teletext remainder', 'MODE 7 boxed / full SAA5050 remainder', 'extend existing teletext renderer'),
    ('Physics', 'FN_b2* Box2D bindings', 'corpus physics tier'),
    ('Network', 'URL fetch / Ceefax remote', 'needs HTTP client'),
    ('Compiler', 'BBC BASIC compiler / Crunch', 'not interpreter scope'),
]


def deferred_rows() -> List[DeferredRow]:
    return list(DEFERRED_ROWS)
