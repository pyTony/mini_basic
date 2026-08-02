import io
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

BASE = {
    40: 'W%=38', 50: 'H%=26', 60: 'DIM L%(W%,H%), N%(W%,H%)',
    90: 'FOR I%=1 TO W%', 100: 'FOR J%=1 TO H%',
    110: 'IF RND(1)>=.7 N%(I%,J%)=1 ELSE N%(I%,J%)=0',
    120: 'NEXT', 130: 'NEXT', 240: 'G%=0', 250: 'COLOUR 15',
}
COMPUTE = {
    350: 'FOR I%=1 TO W%', 360: 'FOR J%=1 TO H%', 370: 'C%=0',
    380: 'FOR K%=I%-1 TO I%+1', 390: 'IF K%=0 OR K%>W% THEN 440',
    400: 'FOR M%=J%-1 TO J%+1', 410: 'IF M%=0 OR M%>H% OR (K%=I% AND M%=J%) GOTO 430',
    420: 'C%=C%+L%(K%,M%)', 430: 'NEXT', 440: 'NEXT',
    450: 'IF C%=2 THEN N%(I%,J%)=L%(I%,J%) ELSE N%(I%,J%)=-(C%=3)',
    460: 'NEXT', 470: 'NEXT', 480: 'G%=G%+1', 485: 'WAIT 0',
    490: 'IF G%>2 END ELSE GOTO 250', 500: 'END',
}
VDU_DISPLAY = {
    280: 'FOR J%=1 TO H%', 290: 'PRINT TAB(1,J%);', 300: 'FOR I%=1 TO W%',
    310: 'C%=N%(I%,J%): L%(I%,J%)=C%', 320: 'IF C% VDU 42 ELSE VDU 32',
    330: 'NEXT', 340: 'NEXT',
}
ROW_DISPLAY = {
    280: 'FOR J%=1 TO H%', 290: 'R$=""', 300: 'FOR I%=1 TO W%',
    310: 'C%=N%(I%,J%): L%(I%,J%)=C%', 320: 'IF C% R$=R$+"*" ELSE R$=R$+" "',
    330: 'NEXT', 340: 'PRINT TAB(1,J%);R$;', 345: 'NEXT',
}


def bench(display, label):
    prog = {**BASE, **display, **COMPUTE}
    interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
    interp.program = prog
    interp._program_stdout = io.StringIO()
    start = time.perf_counter()
    interp.run()
    print(f'{label}: {time.perf_counter() - start:.2f}s')


bench(VDU_DISPLAY, 'vdu')
bench(ROW_DISPLAY, 'row')