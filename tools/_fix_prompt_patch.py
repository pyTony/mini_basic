from pathlib import Path

p = Path("test/test_mini_basic.py")
t = p.read_text(encoding="utf-8")
old = "mini_basic.runtime._prompt_editing_input"
# Patch both import sites used after modularization.
# Tests use a single string; use dialect as primary (auto_entry).
# For edit_line (core), also need core — replace with a helper in tests is better.
# Use dialect path; dual-patch via context manager would need multi-line edits.
# Instead re-export from runtime and make dialect/core call via helpers module attr.

new = "mini_basic.runtime_parts.helpers._prompt_editing_input"
# That only works if callers use helpers._prompt_editing_input dynamically.
# They bind at import time — need to patch dialect AND core.
print("count old", t.count(old))
