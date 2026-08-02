import io
import os
import sys
from contextlib import redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from mini_basic import BASICInterpreter

interp = BASICInterpreter()
interp.program = {
    10: "FOR I = 1 TO 200",
    20: 'PRINT I;" ";',
    30: "NEXT",
}

buf = io.StringIO()
with redirect_stdout(buf):
    interp.run()

out = buf.getvalue()
print("line_count:", len(out.splitlines()))
print("has ' 0':", " 0" in out)
print("around 94:", repr(out[175:210]))
print("tail:", repr(out[-30:]))