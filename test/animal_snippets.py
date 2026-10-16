"""Short BBC excerpts of animal.txt behaviour — do not LOAD the full game."""
from __future__ import annotations

from mini_basic import BASICInterpreter
from mini_basic.config import InterpreterConfig

# Article stripper + nospace (animal DEF FNstrip / FNnospace + DATA).
FNSTRIP_LINES = [
    (100, 'DEF FNstrip(name$)'),
    (110, 'name$=FNnospace(name$)'),
    (120, 'LOCAL AT$,Z'),
    (130, 'RESTORE +1'),
    (140, 'REPEAT Z=Z+1:READ AT$'),
    (150, 'UNTIL AT$=LEFT$(name$,LEN(AT$)) OR Z=10'),
    (160, 'IF Z<10 THEN name$=MID$(name$,1+LEN(AT$))'),
    (170, '=FNnospace(name$)'),
    (180, 'DATA A ,AN ,THE ,a ,an ,the ,An ,The ,THe ,,'),
    (200, 'DEF FNnospace(name$)'),
    (210, 'name$=" "+name$'),
    (220, 'REPEAT name$=MID$(name$,2)'),
    (230, 'UNTIL LEFT$(name$,1)<>" "'),
    (240, '=name$'),
]

FNART_LINES = [
    (300, 'DEF FNart(noun$)'),
    (310, 'IF INSTR("AEIOUaeiou",LEFT$(noun$,1)) THEN ="an "+noun$ ELSE ="a "+noun$'),
]

# Enough of FNquery to append (Y/N) and return Y/N.
FNQUERY_LINES = [
    (400, 'DEF FNquery(prompt$)'),
    (410, 'LOCAL A$'),
    (420, 'IF INSTR(prompt$,"(Y/N)")=0 AND RIGHT$(prompt$,1)<>"?" THEN prompt$=prompt$+" (Y/N)"'),
    (430, 'PRINT prompt$;'),
    (440, 'INPUT A$'),
    (450, 'A$=LEFT$(A$,1)'),
    (460, 'IF A$="y" THEN A$="Y"'),
    (470, 'IF A$="n" THEN A$="N"'),
    (480, '=A$'),
]


def bbc_none() -> BASICInterpreter:
    return BASICInterpreter(
        InterpreterConfig(dialect='bbc', display='none', display_locked=True)
    )


def load_lines(interp: BASICInterpreter, lines: list[tuple[int, str]]) -> BASICInterpreter:
    for line_num, statement in lines:
        interp.set_program_line(line_num, statement)
    interp._prepare_run()
    return interp
