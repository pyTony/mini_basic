"""Detokenize Acorn 6502 (Wilson) and Russell BBC BASIC program files."""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

# Acorn 6502 (Wilson) keyword tokens (&80..&FF).
_BBC_KEYWORDS_WILSON: Tuple[str, ...] = (
    'AND', 'DIV', 'EOR', 'MOD', 'OR', 'ERROR', 'LINE', 'OFF',
    'STEP', 'SPC', 'TAB(', 'ELSE', 'THEN', '<LINE>', 'OPENIN', 'PTR',
    'PAGE', 'TIME', 'LOMEM', 'HIMEM', 'ABS', 'ACS', 'ADVAL', 'ASC',
    'ASN', 'ATN', 'BGET', 'COS', 'COUNT', 'DEG', 'ERL', 'ERR',
    'EVAL', 'EXP', 'EXT', 'FALSE', 'FN', 'GET', 'INKEY', 'INSTR(',
    'INT', 'LEN', 'LN', 'LOG', 'NOT', 'OPENUP', 'OPENOUT', 'PI',
    'POINT(', 'POS', 'RAD', 'RND', 'SGN', 'SIN', 'SQR', 'TAN',
    'TO', 'TRUE', 'USR', 'VAL', 'VPOS', 'CHR$', 'GET$', 'INKEY$',
    'LEFT$(', 'MID$(', 'RIGHT$(', 'STR$', 'STRING$(', 'EOF',
    'AUTO', 'DELETE', 'LOAD', 'LIST', 'NEW', 'OLD', 'RENUMBER', 'SAVE',
    'PUT', 'PTR', 'PAGE', 'TIME', 'LOMEM', 'HIMEM', 'SOUND', 'BPUT',
    'CALL', 'CHAIN', 'CLEAR', 'CLOSE', 'CLG', 'CLS', 'DATA', 'DEF',
    'DIM', 'DRAW', 'END', 'ENDPROC', 'ENVELOPE', 'FOR', 'GOSUB', 'GOTO',
    'GCOL', 'IF', 'INPUT', 'LET', 'LOCAL', 'MODE', 'MOVE', 'NEXT',
    'ON', 'VDU', 'PLOT', 'PRINT', 'PROC', 'READ', 'REM', 'REPEAT',
    'REPORT', 'RESTORE', 'RETURN', 'RUN', 'STOP', 'COLOUR', 'TRACE',
    'UNTIL', 'WIDTH', 'OSCLI',
)

# R.T.Russell / BBC BASIC for Windows & SDL 2.0 (&80..&FF).
_BBC_KEYWORDS_RUSSELL: Tuple[str, ...] = (
    'AND', 'DIV', 'EOR', 'MOD', 'OR', 'ERROR', 'LINE', 'OFF',
    'STEP', 'SPC', 'TAB(', 'ELSE', 'THEN', '<LINE>', 'OPENIN', 'PTR',
    'PAGE', 'TIME', 'LOMEM', 'HIMEM', 'ABS', 'ACS', 'ADVAL', 'ASC',
    'ASN', 'ATN', 'BGET', 'COS', 'COUNT', 'DEG', 'ERL', 'ERR',
    'EVAL', 'EXP', 'EXT', 'FALSE', 'FN', 'GET', 'INKEY', 'INSTR(',
    'INT', 'LEN', 'LN', 'LOG', 'NOT', 'OPENUP', 'OPENOUT', 'PI',
    'POINT(', 'POS', 'RAD', 'RND', 'SGN', 'SIN', 'SQR', 'TAN',
    'TO', 'TRUE', 'USR', 'VAL', 'VPOS', 'CHR$', 'GET$', 'INKEY$',
    'LEFT$(', 'MID$(', 'RIGHT$(', 'STR$', 'STRING$(', 'EOF',
    'SUM', 'WHILE', 'CASE', 'WHEN', 'OF', 'ENDCASE', 'OTHERWISE', 'ENDIF',
    'ENDWHILE', 'PTR', 'PAGE', 'TIME', 'LOMEM', 'HIMEM', 'SOUND', 'BPUT',
    'CALL', 'CHAIN', 'CLEAR', 'CLOSE', 'CLG', 'CLS', 'DATA', 'DEF',
    'DIM', 'DRAW', 'END', 'ENDPROC', 'ENVELOPE', 'FOR', 'GOSUB', 'GOTO',
    'GCOL', 'IF', 'INPUT', 'LET', 'LOCAL', 'MODE', 'MOVE', 'NEXT',
    'ON', 'VDU', 'PLOT', 'PRINT', 'PROC', 'READ', 'REM', 'REPEAT',
    'REPORT', 'RESTORE', 'RETURN', 'RUN', 'STOP', 'COLOUR', 'TRACE',
    'UNTIL', 'WIDTH', 'OSCLI',
)

# Russell extended tokens (&00..&1F) used in saved programs.
_BBC_EXTENDED_KEYWORDS_RUSSELL: Tuple[str, ...] = (
    '', 'CIRCLE', 'ELLIPSE', 'FILL', 'MOUSE', 'ORIGIN', 'QUIT', 'RECTANGLE',
    'SWAP', 'SYS', 'TINT', 'WAIT', 'INSTALL', '<EOL>', 'PRIVATE', 'BY',
    'EXIT', '', '', '', '', '', '', '',
    '', '', '', '', '', '', '', '',
)

_KEYWORDS_NEED_SPACE_AFTER = frozenset({
    'FOR', 'TO', 'STEP', 'IF', 'THEN', 'ELSE', 'GOTO', 'GOSUB', 'ON',
    'LET', 'DIM', 'INPUT', 'READ', 'DATA', 'PRINT', 'NEXT', 'RETURN',
    'STOP', 'END', 'RUN', 'MODE', 'GCOL', 'MOVE', 'DRAW', 'PLOT',
    'VDU', 'COLOUR', 'COLOR', 'REM', 'RESTORE', 'REPEAT',
    'UNTIL', 'WHILE', 'WEND', 'LOCAL', 'DEF', 'OSCLI', 'CLS', 'CLG',
    'CHAIN', 'CASE', 'WHEN', 'OF', 'OTHERWISE', 'CIRCLE', 'FILL', 'ORIGIN',
    'WAIT', 'RECTANGLE', 'ELLIPSE', 'EXIT', 'SUM',
})


def detect_bbc_binary_format(data: bytes) -> Optional[str]:
    if len(data) < 4:
        return None
    tail = data[-4:]
    if tail == b'\r\x00\xff\xff':
        return 'russell'
    if len(data) >= 2 and data[-2:] == b'\r\xff':
        return 'wilson'
    if tail[-2:] == b'\r\xff':
        return 'wilson'
    if data[0] == 0x0D and len(data) >= 6 and data[-1] == 0xFF:
        return 'wilson'
    return None


def _keyword_table(fmt: str) -> Tuple[str, ...]:
    if fmt == 'russell':
        return _BBC_KEYWORDS_RUSSELL
    return _BBC_KEYWORDS_WILSON


def _keyword_name(byte_val: int, fmt: str = 'wilson') -> str:
    if 0x80 <= byte_val <= 0xFF:
        return _keyword_table(fmt)[byte_val - 0x80]
    if fmt == 'russell' and 0x00 <= byte_val <= 0x1F:
        return _BBC_EXTENDED_KEYWORDS_RUSSELL[byte_val]
    return chr(byte_val)


def _decode_line_number_ref(data: bytes, index: int) -> Tuple[int, int]:
    if index + 4 > len(data) or data[index] != 0x8D:
        raise ValueError('bad line number reference')
    b1, b2, b3 = data[index + 1], data[index + 2], data[index + 3]
    # Correct decoding for BBC BASIC in-line line number references (after &8D).
    # Line numbers in GOTO/GOSUB etc are packed into 3 bytes with bit shuffling.
    # Formula verified against real BBCSDL output for programs like RACE.BBC.
    line = (b2 & 0x3F) | ((b3 & 0x3F) << 8)
    extra = (b1 & 0xC0) | ((b1 & 0x30) << 2) | ((b1 & 0x0C) << 4) | ((b1 & 0x03) << 6)
    if b1 & 0x10:
        extra &= ~0x40
    line |= extra
    # Sanity check: line numbers must be in valid BBC range.
    if not (1 <= line <= 65535):
        raise ValueError(f"Sanity check failed: decoded invalid line number {line}")
    return line, index + 4


def _needs_space_after_keyword(keyword: str, nxt: Optional[int], fmt: str) -> bool:
    if nxt is None:
        return False
    if keyword not in _KEYWORDS_NEED_SPACE_AFTER:
        return False
    if nxt in (0x0D, 0x3A, 0x28, 0x29, 0x2C, 0x3B):
        return False
    if nxt == 0x22:
        return True
    if 0x30 <= nxt <= 0x39:
        return True
    if 0x41 <= nxt <= 0x5A or 0x61 <= nxt <= 0x7A:
        return True
    if nxt >= 0x80:
        return True
    if fmt == 'russell' and 0x01 <= nxt <= 0x1F:
        return True
    return False


def detokenize_line_body(body: bytes, *, fmt: str = 'wilson') -> str:
    out: List[str] = []
    index = 0
    in_string = False
    after_rem = False

    while index < len(body):
        byte_val = body[index]
        if byte_val == 0x0D:
            break
        if after_rem:
            out.append(chr(byte_val))
            index += 1
            continue
        if in_string:
            if byte_val == 0x22:
                in_string = False
            out.append(chr(byte_val))
            index += 1
            continue
        if byte_val == 0x22:
            in_string = True
            out.append('"')
            index += 1
            continue
        if byte_val == 0x8D:
            line, index = _decode_line_number_ref(body, index)
            out.append(str(line))
            continue
        is_keyword = byte_val >= 0x80
        if fmt == 'russell' and 0x01 <= byte_val <= 0x1F:
            keyword = _BBC_EXTENDED_KEYWORDS_RUSSELL[byte_val]
            if keyword and keyword != '<EOL>':
                nxt = body[index + 1] if index + 1 < len(body) else None
                if nxt == 0x0D:
                    nxt = None
                out.append(keyword)
                if _needs_space_after_keyword(keyword, nxt, fmt):
                    out.append(' ')
                index += 1
                continue
        if is_keyword:
            keyword = _keyword_name(byte_val, fmt)
            if keyword == '<LINE>':
                line, index = _decode_line_number_ref(body, index)
                out.append(str(line))
                continue
            if keyword == 'REM':
                after_rem = True
            nxt = body[index + 1] if index + 1 < len(body) else None
            if nxt == 0x0D:
                nxt = None
            out.append(keyword)
            if _needs_space_after_keyword(keyword, nxt, fmt):
                out.append(' ')
            index += 1
            continue
        out.append(chr(byte_val))
        index += 1

    result = ''.join(out).rstrip()
    # BBCSDL lists forever-loops as ``UNTIL.`` (period in the token stream, not
    # the FALSE keyword). Same meaning as ``UNTIL FALSE``.
    result = re.sub(r'\bUNTIL\s*\.\s*$', 'UNTIL FALSE', result, flags=re.IGNORECASE)
    # Normalize compound assignments (combined LET / op=) to clean form like "a -= "
    result = re.sub(r'([A-Za-z0-9_])\s*-\s*=\s*', r'\1 -= ', result)
    result = re.sub(r'([A-Za-z0-9_])\s*\+\s*=\s*', r'\1 += ', result)
    result = re.sub(r'([A-Za-z0-9_])\s*\*\s*=\s*', r'\1 *= ', result)
    result = re.sub(r'([A-Za-z0-9_])\s*/\s*=\s*', r'\1 /= ', result)
    return result.rstrip()


def parse_wilson_program(data: bytes) -> List[Tuple[int, str]]:
    """Parse Acorn 6502 Wilson format: chained lines with 4-byte trailer."""
    if not data or data[0] != 0x0D:
        raise ValueError('not Wilson-format BBC BASIC')
    index = 1
    line_num = (data[index] << 8) | data[index + 1]
    index += 2
    if index >= len(data):
        return []
    line_len = data[index]
    index += 1
    lines: List[Tuple[int, str]] = []

    while index < len(data) and line_len > 0:
        if index + line_len > len(data):
            break
        body = data[index:index + line_len]
        index += line_len

        current_line = line_num
        if len(body) >= 4 and body[-4] == 0x0D:
            text = body[:-4]
            line_num = (body[-3] << 8) | body[-2]
            line_len = body[-1]
        elif body and body[-1] == 0x0D:
            text = body[:-1]
            line_len = 0
        else:
            text = body
            line_len = 0

        if not (0 <= current_line <= 65535):
            break  # sanity check on header line number

        lines.append((current_line, detokenize_line_body(text, fmt='wilson')))

        if line_len == 0:
            break

    return lines


def parse_russell_program(data: bytes) -> List[Tuple[int, str]]:
    """Parse R.T.Russell / BBCSDL tokenized format.

    Record layout (common for .bbc files):
      [1 byte length of this record (including the length byte)]
      [2 bytes line number little-endian]
      [tokenized body ... 0x0D]
    """
    index = 0
    lines: List[Tuple[int, str]] = []
    while index < len(data):
        if index + 3 > len(data):
            break
        line_len = data[index]
        if line_len < 4:
            break
        if index + line_len > len(data):
            break
        line_num = data[index + 1] | (data[index + 2] << 8)
        if not (0 <= line_num <= 65535):
            break  # sanity
        body = data[index + 3 : index + line_len]
        index += line_len
        if not body or body[-1] != 0x0D:
            break
        lines.append((line_num, detokenize_line_body(body[:-1], fmt='russell')))
    return lines


def bbc_binary_to_source(data: bytes) -> List[str]:
    fmt = detect_bbc_binary_format(data)
    if fmt == 'wilson':
        lines = parse_wilson_program(data)
    elif fmt == 'russell':
        lines = parse_russell_program(data)
    else:
        raise ValueError('unrecognised BBC BASIC binary format')
    out = []
    defined_lines = set()
    for num, text in lines:
        if num:
            if num in defined_lines:
                # duplicate line num, unusual but tolerate
                pass
            defined_lines.add(num)
        if not text and not num:
            continue
        if num:
            out.append(f'{num} {text}')
        else:
            # Unnumbered line (common at start of BBCSDL examples)
            out.append(text)

    # Sanity check: scan for GOTO/GOSUB/RESTORE/THEN <num> and verify the target
    # line numbers are valid (1-65535). We don't require existence because
    # programs can have forward refs or runtime-computed, but bad decode would
    # produce 0 or huge numbers.
    ref_pattern = re.compile(r'\b(?:GOTO|GOSUB|RESTORE|THEN)\s+(\d+)')
    for line in out:
        for m in ref_pattern.finditer(line):
            ref = int(m.group(1))
            if not (1 <= ref <= 65535):
                raise ValueError(f"Sanity check failed: invalid GOTO/GOSUB target {ref} in '{line}'")
    return out
