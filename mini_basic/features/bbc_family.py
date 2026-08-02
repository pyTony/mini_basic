"""BBC BASIC *family* dialects — where they diverge (not mini vs mits).

Columns:
  Beeb   — BBC Micro / Master (MOS BASIC II/IV, tokenized .bbc)
  ROS    — RISC OS Archimedes BASIC V/VI
  BB4W   — BBC BASIC for Windows
  SDL    — BBC BASIC for SDL (BB4W lineage + extensions)
  mini   — this interpreter (bbc dialect mode)

  + = supported   - = absent / rejected   ~ = partial or different semantics
  ? = varies by version / optional
"""
from __future__ import annotations

from typing import List, Tuple

# Feature, Beeb, ROS, BB4W, SDL, mini, notes
BbcFamilyRow = Tuple[str, str, str, str, str, str, str]


def bbc_family_rows() -> List[BbcFamilyRow]:
    return [
        # --- source form / PROC ---
        (
            'PROC/FN glued to name',
            '+',
            '+',
            '+',
            '+',
            '+',
            'No space: PROCfoo not PROC foo (ROS: Bad call if spaced)',
        ),
        (
            'DEFPROC / DEF PROC',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Both forms; PROC still glued to name after DEF',
        ),
        (
            'LIST spacing PROC name',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Export must re-glue; mini LIST now glues for ROS paste',
        ),
        (
            'CASE / WHEN / OF',
            '-',
            '+',
            '+',
            '+',
            '+',
            'Not on classic Beeb MOS',
        ),
        (
            'WHILE / ENDWHILE',
            '-',
            '+',
            '+',
            '+',
            '+',
            'Beeb: REPEAT only',
        ),
        (
            'SYS / OSCLI *',
            '~',
            '+',
            '+',
            '+',
            '~',
            'Beeb *FX; ROS SYS; BB4W/SDL rich SYS',
        ),
        (
            '@lib$ @dir$ path vars',
            '-',
            '-',
            '+',
            '+',
            '~',
            'BB4W/SDL; mini stubs some',
        ),
        (
            'INSTALL / LIBRARY',
            '-',
            '~',
            '+',
            '+',
            '~',
            'BB4W/SDL library path',
        ),
        # --- graphics ---
        (
            'MODE 0–7 Beeb',
            '+',
            '~',
            '+',
            '+',
            '+',
            'ROS modes differ; MODE 7 teletext ROS ≠ Beeb',
        ),
        (
            'MODE 8+ (PC/SDL)',
            '-',
            '-',
            '+',
            '+',
            '+',
            'BB4W/SDL extended modes',
        ),
        (
            'VDU 5 graphics text',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Cursor = top-left of cell (welcome letters)',
        ),
        (
            'VDU 23 redefine char',
            '+',
            '+',
            '+',
            '+',
            '+',
            'welcome CHR$255 solid block',
        ),
        (
            'VDU 24 graphics window',
            '+',
            '+',
            '+',
            '+',
            '+',
            'CLG clips to window (welcome red frame)',
        ),
        (
            'ORIGIN / VDU 29',
            '+',
            '+',
            '+',
            '+',
            '+',
            'welcome disc icon origin',
        ),
        (
            'PLOT 0–255 Beeb set',
            '+',
            '+',
            '+',
            '+',
            '~',
            'mini subset + BB4W extras (CIRCLE…)',
        ),
        (
            'CIRCLE / ELLIPSE keywords',
            '-',
            '~',
            '+',
            '+',
            '+',
            'Beeb: PLOT codes; ROS has some',
        ),
        (
            'GCOL action 0–7',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Invert = PLOT …6; welcome zaps',
        ),
        (
            'Colour 7 = white',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Not VGA gray; letters GCOL 0,7',
        ),
        # --- I/O & sound ---
        (
            'INKEY / INKEY$',
            '+',
            '+',
            '+',
            '+',
            '+',
            'INKEY n cs; INKEY1 glued → INKEY(1)',
        ),
        (
            'ENVELOPE / SOUND',
            '+',
            '~',
            '+',
            '+',
            '~',
            'mini ENVELOPE no-op; SOUND limited',
        ),
        (
            'MOUSE',
            '-',
            '+',
            '+',
            '+',
            '+',
            'Desktop / BB4W/SDL',
        ),
        (
            'ON CLOSE',
            '-',
            '~',
            '+',
            '+',
            '+',
            'Window close trap (SDL/BB4W)',
        ),
        # --- numbers ---
        (
            'Integer % vars',
            '+',
            '+',
            '+',
            '+',
            '+',
            '32-bit on classic; mini bigint option',
        ),
        (
            'DIV toward zero',
            '+',
            '+',
            '+',
            '+',
            '~',
            'mini historically floor-div; check suite',
        ),
        (
            'TRUE = -1',
            '+',
            '+',
            '+',
            '+',
            '+',
            'All BBC family',
        ),
        (
            'Line numbers required',
            '+',
            '-',
            '-',
            '-',
            '~',
            'Beeb classic; ROS/BB4W unnumbered OK',
        ),
        (
            'Tokenized program files',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Formats differ; mini detokenizes Beeb/SDL',
        ),
        # --- welcome corpus pitfalls ---
        (
            'welcome.bbc corpus',
            '~',
            '~',
            '+',
            '+',
            '+',
            'Written for SDL; ROS needs glued PROC LIST',
        ),
        (
            'Bare IF cond: body',
            '+',
            '+',
            '+',
            '+',
            '+',
            'IF(I%AND1)=0:PLOT… (no THEN)',
        ),
        (
            'ASC"B" without ( )',
            '+',
            '+',
            '+',
            '+',
            '+',
            'Glued string literal form',
        ),
    ]


def format_bbc_family_matrix(rows: List[BbcFamilyRow] | None = None) -> str:
    if rows is None:
        rows = bbc_family_rows()
    lines = [
        '=== BBC BASIC family dialects (Beeb / RISC OS / BB4W / SDL / mini) ===',
        '  Beeb=BBC Micro MOS   ROS=Archimedes BASIC V/VI',
        '  BB4W=BBC BASIC for Windows   SDL=BBC BASIC for SDL   mini=this app (bbc mode)',
        '',
        f'  {"Feature":<28} {"Beeb":^4} {"ROS":^4} {"BB4W":^4} {"SDL":^4} {"mini":^4}  notes',
        f'  {"-" * 28} ---- ---- ---- ---- ----  -----',
    ]
    for feature, beeb, ros, bb4w, sdl, mini, notes in rows:
        lines.append(
            f'  {feature:<28} {beeb:^4} {ros:^4} {bb4w:^4} {sdl:^4} {mini:^4}  {notes}'
        )
    lines.extend(
        [
            '',
            '  + = yes   - = no   ~ = partial / different',
            '',
            '  Archimedes paste tip: use  --list --dialect bbc --display none',
            '  (LIST re-glues PROCname). Do not hand-edit spaces into PROC names.',
            '  "Bad call of function/procedure" almost always means PROC Name with a space.',
        ]
    )
    return '\n'.join(lines)
