"""Replace broken tokenized animal.bbc with UTF-8 source from corpus (loads as text)."""
from pathlib import Path
from datetime import datetime, timezone

root = Path(".")
src = root / "test/corpus/bbcsdl/games/animal.txt"
bbc = root / "examples/games/animal.bbc"
bas = root / "examples/games/animal.bas"
bak = root / "examples/games/animal.bbc.broken_binary_2026-07-26"

text = src.read_text(encoding="utf-8")
# Ensure leading comment for git/history
header = (
    "REM mini_basic: UTF-8 listing (was Russell tokenized .bbc; binary corrupted by\n"
    "REM length-breaking @% patch 2026-07-26). Source of truth also in\n"
    "REM test/corpus/bbcsdl/games/animal.txt. @%=0 avoids STR$ pad / N? tree bug.\n"
    ":\n"
)
# If corpus already has REM about @%, just prefix provenance once
body = text
if "UTF-8 listing" not in body:
    # insert after first ON ERROR line block if present
    body = header + body

# archive broken binary once
if bbc.is_file() and bbc.read_bytes()[:1] == b"D":
    bak.write_bytes(bbc.read_bytes())
    print("archived broken binary to", bak, "size", bak.stat().st_size)

bbc.write_text(body, encoding="utf-8", newline="\n")
bas.write_text(body, encoding="utf-8", newline="\n")
print("wrote", bbc, "bytes", bbc.stat().st_size)
print("wrote", bas, "bytes", bas.stat().st_size)

from mini_basic import BASICInterpreter, InterpreterConfig
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

i = BASICInterpreter(InterpreterConfig(dialect="bbc", display="none"))
i.load(str(bbc))
print("loaded lines", len(i.program))
assert len(i.program) > 50, "too few lines"
# smoke: answer n
inputs = iter(["n", "n"])
out = StringIO()
with redirect_stdout(out), patch.object(i, "_read_program_input", side_effect=lambda *a, **k: next(inputs, "n")), patch("time.sleep"), patch.object(i, "_execute_wait", side_effect=KeyboardInterrupt):
    try:
        i.run()
    except (KeyboardInterrupt, SystemExit):
        pass
print(out.getvalue()[:400])
assert "ANIMAL" in out.getvalue()
print("SMOKE OK")
