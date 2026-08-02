from __future__ import annotations

from typing import List

from .types import MatrixRow


def dialect_structure_rows() -> List[MatrixRow]:
    return [
        ('Numbered lines', '+', '+', '+', '-', '+'),
        ('Unnumbered lines', '-', '-', '-', '+', '+'),
        ('GOTO / GOSUB / RETURN', '+', '+', '+', '+', '+'),
        ('IF ... GOTO nn', '+', '+', '-', '-', '+'),
        ('IF ... THEN nn (implicit GOTO)', '+', '+', '-', '+', '+'),
        ('ON GOTO / ON GOSUB', '+', '+', '+', '+', '+'),
        ('ON ERROR GOTO/GOSUB / RESUME', '+', '+', '+', '+', '+'),
        ('IF/ENDIF / ELSEIF', '-', '-', '-', '+', '+'),
        ('WHILE / WEND', '-', '-', '-', '+', '+'),
        ('REPEAT / UNTIL', '-', '-', '-', '+', '+'),
        ('EXIT FOR/WHILE/REPEAT', '-', '-', '-', '+', '+'),
        ('PROC / DEF PROC / ENDPROC', '-', '-', '-', '+', '+'),
        ('BREAK / CONTINUE (mini ext)', '-', '-', '-', '-', '+'),
        ('INSTR', '-', '-', '-', '+', '+'),
        ('DEF FN one-line', '+', '+', '+', '+', '+'),
        ('DEF FN ... END DEF', '-', '-', '-', '~', '+'),
        ('? shorthand (PRINT)', '+', '+', '+', '+', '+'),
        ('TRUE/FALSE (-1/0)', '+', '+', '+', '+', '+'),
        ('ARG / CLI args', '-', '-', '-', '-', '+'),
        ('FG$ / BG$ / ANSI colors', '-', '-', '-', '-', '+'),
        ('TIME (centisecond clock)', '+', '+', '+', '+', '+'),
        ('Case-sensitive names', '-', '-', '-', '-', '+'),
        ('LIST/SAVE detokenize', '+', '+', '+', '+', '-'),
    ]
