import io
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

path = os.path.join(_ROOT, 'test', 'corpus', 'agon', 'life.bas')
prog = {}
for raw in open(path, encoding='utf-8'):
    m = re.match(r'^\s*(\d+)\s+(.*)$', raw.rstrip())
    if m:
        prog[int(m.group(1))] = m.group(2)

# Run through first display only
prog[345] = 'END'

interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
interp.program = prog
buf = io.StringIO()
interp._program_stdout = buf
interp.run()

out = buf.getvalue()
stars = out.count('*')
spaces_interior = out.count(' ')
print('stars in output', stars)
print('R$ after run', repr(interp.str_variables.get('R')))
print('sample lines with star', [l for l in out.splitlines() if '*' in l][:3])
print('errors', [l for l in out.splitlines() if l.startswith('?')])