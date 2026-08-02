"""Run a few Conway generations and show a text snapshot (ANSI stripped)."""
import io
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter, InterpreterConfig

_CORPUS = os.path.join(_ROOT, 'test', 'corpus', 'agon', 'life.bas')

program = {}
with open(_CORPUS, encoding='utf-8', errors='replace') as handle:
    for raw in handle:
        match = re.match(r'^\s*(\d+)\s+(.*)$', raw.rstrip())
        if match:
            program[int(match.group(1))] = match.group(2)

program[485] = 'IF G%>3 END'

interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
interp.program = program
buf = io.StringIO()
interp._program_stdout = buf
interp.run()

plain = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', buf.getvalue())
plain = plain.replace('\r', '')

# Extract generation labels and a rough grid slice after the last one.
gens = re.findall(r'Generation:\s*(\d+)', plain)
print(f'Generations completed: {gens[-1] if gens else "?"} (saw {", ".join(gens)})')
print()

# Show lines that look like the bordered grid (plus signs and stars/spaces).
grid_lines = [
    line for line in plain.splitlines()
    if line and set(line.strip()) <= {'+', '*', ' '}
    and len(line.strip()) > 10
]
if grid_lines:
    print('Final board snapshot (last ~12 rows):')
    for line in grid_lines[-12:]:
        print(line)
else:
    snippet = plain[-800:] if len(plain) > 800 else plain
    print(snippet)