# Runtime modularization status (2026-07-17)

## Live layout (modular)

`BASICInterpreter` is a **mixin composition** facade. All 495 methods from the
former monorepo live under `runtime_parts/`; CLI/REPL helpers stay in
`runtime.py`.

| Path | Role | Size (approx) |
|------|------|----------------|
| `runtime.py` | Facade class + REPL/CLI/`main` | ~50 KB |
| `runtime_parts/core.py` | Init, state, clocks, shared helpers | ~79 KB |
| `runtime_parts/program.py` | Program lines, parse, labels, prepare | ~63 KB |
| `runtime_parts/expr.py` | Expr eval, vars, arrays, assign | ~124 KB |
| `runtime_parts/defs.py` | DEF FN / DEF PROC | ~12 KB |
| `runtime_parts/execution.py` | RUN loop, statements, control flow | ~155 KB |
| `runtime_parts/io.py` | PRINT/INPUT/files/LIST/SAVE/LOAD | ~61 KB |
| `runtime_parts/graphics.py` | Display, MODE/VDU, INKEY, sound | ~27 KB |
| `runtime_parts/dialect.py` | Dialect switches / hints | ~7 KB |
| `runtime_parts/helpers.py` | Free functions methods call by name | ~7 KB |

Public API is unchanged:

```python
from mini_basic import BASICInterpreter, main
```

## Archives / restore

| Path | Notes |
|------|--------|
| `backup/runtime_monolith.py` | Full pre-split monorepo (~555 KB) |
| `backup/runtime_old.py` | Same content (user restore source) |
| `backup/obsolete_runtime_stubs/` | Old incomplete stubs + monorepo snapshots |

Restore monorepo (if needed):

```powershell
Copy-Item -LiteralPath 'backup\runtime_monolith.py' -Destination 'mini_basic\runtime.py' -Force
```

Then re-split:

```powershell
python tools/split_runtime_mixins.py
```

## Regenerating mixins

`tools/split_runtime_mixins.py` AST-splits a monorepo `runtime.py` into mixins:

1. Classifies methods by name into buckets (core/program/expr/defs/execution/io/graphics/dialect).
2. Emits mixin modules + helpers for free functions methods reference.
3. Writes the facade `runtime.py`.

```text
python tools/split_runtime_mixins.py --classify-only   # list buckets
python tools/split_runtime_mixins.py --dry-run
python tools/split_runtime_mixins.py                   # write files
```

**Source must be the monorepo** (or re-run from `backup/runtime_monolith.py`
via `--source`). Do not feed the thin facade back into the splitter.

## Verified

- `python -m mini_basic --help`
- `from mini_basic import BASICInterpreter` + init
- OPENOUT / file I/O path (`_parse_path_arg` helpers import)
- `pytest -m phase1` → **35 passed, 1 skipped**

## Obsolete stubs (removed from active use)

Earlier incomplete files at package root (`runtime_core.py`,
`runtime_execution.py`, …) were **not** wired into the live import path.
They are superseded by `runtime_parts/*` and may be deleted or ignored.
