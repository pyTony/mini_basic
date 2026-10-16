import os
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
from mini_basic import BASICInterpreter, InterpreterConfig

i = BASICInterpreter(
    InterpreterConfig(dialect="bbc", display="pygame", hold_display_open=False)
)
i.load("basics/Clock.bas", announce=False)
for n, s in list(i.program.items()):
    u = s.strip().upper()
    if u.startswith("REPEAT") or u.startswith("UNTIL") or u.startswith("WAIT"):
        i.program[n] = "REM"
    if "TIME$" in s.upper():
        i.program[n] = "REM"
ml = max(i.program)
i.program[ml + 10] = "HOUR24%=18:HOUR%=6:MINUTE%=30:SECOND%=15:PROCupdate:END"
out, err = StringIO(), StringIO()
with redirect_stdout(out), redirect_stderr(err), patch("time.sleep"):
    i.run()
print("stdout", repr(out.getvalue()))
print("stderr", repr(err.getvalue()[:300]))
d = i._display
if d is not None:
    row0 = "".join(d._text[0][c][0] for c in range(d.text_cols))
    row1 = "".join(d._text[1][c][0] for c in range(d.text_cols))
    print("row0", repr(row0.rstrip()))
    print("row1", repr(row1.rstrip()))
    assert "18:30:15" in row1 or "18:30:15" in out.getvalue()
    print("OK digital")
