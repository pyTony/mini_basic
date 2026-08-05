# mini_basic

Python BASIC interpreter with multi-dialect support (especially BBC BASIC / BBCSDL-style),
REPL/CLI, file I/O, and optional graphics (terminal / pygame).

**CLI entry points:** `python -m mini_basic` · `mini-basic` / `minibasic` (after pip install) · `python mini_basic.py` · `mb.py`

Version: see `mini_basic/version.py` / `pyproject.toml` (PEP 440, e.g. `1.0.0.dev0`).

## Install (pip / wheel)

The **wheel contains only the interpreter package** (not examples, tests, or tools).

```bash
# From a built wheel (local):
pip install dist/mini_basic-*.whl

# Optional graphics / Windows REPL completion:
pip install "mini-basic[display]"
pip install "mini-basic[all]"

mini-basic --version
python -m mini_basic path/to/program.bas
```

Build locally: `python -m build` — details in [`docs/PACKAGING.md`](docs/PACKAGING.md).  
Full demo trees still use the repo or text-archive installer (`tools/install.ps1`), not the PyPI wheel.

## Quick start (from a source checkout)

```bash
# Text / default display
python -m mini_basic examples/mini/hello_args.bas

# Graphics (pygame)
python -m mini_basic --pygame examples/mini/bbc_graphics_demo.bas

# Interactive REPL
python -m mini_basic
```

```python
from mini_basic import BASICInterpreter, main
from mini_basic.config import InterpreterConfig

interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
```

## Dialects (short)

| Dialect | Notes |
|---------|--------|
| `mini` | Default; case-sensitive identifiers |
| `bbc` | BBC-style; case-sensitive identifiers; keywords upper-only in strict paths |
| `mits` / `commodore` / `tiny` | Classic-style case-folding |

Product conventions that trip people up:

- Use **`MOD`** for modulo (bare `%` is integer-suffix / binary-literal syntax).
- **`SIN` / `COS` / `TAN` use radians** unless you apply `DEG`/`RAD` helpers.
- Missing `IF … THEN <line>` targets **abort RUN** after printing an IF error.

## Layout

| Path | Purpose |
|------|---------|
| `mini_basic/` | Package: runtime facade, mixins, display, REPL helpers |
| `mini_basic/runtime_parts/` | Mixin modules (core, program, expr, defs, execution, io, graphics, dialect) |
| `mini_basic/type_system.py` | `VarKind`, `BasicRuntimeError`, frames / dataclasses |
| `examples/` | Curated demos (bbc/, games/, graphics/, mini/, museum/, …) |
| `basics/` | Small standalone BASIC programs |
| `test/` | Unit tests + BBCSDL corpus + audit probe |
| `documentation/feature_matrices/` | Capability matrices |
| `scripts/` | Dev tools (not collected as tests) |
| `utils/` | Status / progress helpers (`status.html`) |
| `backup/` | Archived monolith / old runtimes |

## Tests (pytest preferred)

From the **project root**:

```bash
# phase0 only — implemented baseline (incl. test_mini_basic, hanoi wrap, …)
python -m pytest -q -m "phase0 and not slow" --timeout=45

# Default REGRESSION — phase0 + phase1 (cumulative; see test/conftest.py)
python -m pytest -q -m "phase1 and not slow" --timeout=45

# When phase2 graphics suites are marked:
python -m pytest -q -m "phase2 and not slow" --timeout=60
```

Markers: `phase0` ⊂ `phase1` ⊂ `phase2` when you use `-m phaseN` (expanded in conftest).
Also: `non_gfx`, `graphics`, `slow`. Module lists live in `pytest.ini`.

Collection is limited to `test/` so scripts under `scripts/` are not mistaken for tests.

Legacy unittest still works for single modules:

```bash
python -m unittest test.test_mini_basic -v
```

### BBCSDL corpus audit

```bash
python test/corpus_audit_probe.py          # writes CORPUS_AUDIT.txt
# list of programs: CORPUS_RUNNABLE.txt
```

## Development notes

- **Git:** branch-per-focus; see `GIT_QUICKSTART.md` and `DEVELOPMENT_GIT_USAGE.md`.
- **Status:** agents update `CURRENT_TASK.txt` / `FEATURES_DONE.txt`; heartbeat refreshes `status.html`
  (`python scripts/progress_heartbeat.py`).
- **Local vs full tree:** see earlier notes in `docs/git/INDEPENDENT_FIXES.md` if you maintain a light
  dev clone vs a full OneDrive tree.

## Import map

```python
from mini_basic import BASICInterpreter, main
from mini_basic.config import InterpreterConfig, DEFAULT_CONFIG
from mini_basic.format import UsingFormatter
from mini_basic.expr import CompiledExpr, patterns
```

Package-level detail: `mini_basic/README.md`.
