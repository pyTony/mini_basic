import io
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
interp.program = {
    10: 'R$=""',
    20: 'C%=1',
    30: 'IF C% R$=R$+"*" ELSE R$=R$+" "',
    40: 'PRINT "["; R$; "]"',
    50: 'END',
}
buf = io.StringIO()
interp._program_stdout = buf
interp.run()
print(buf.getvalue())