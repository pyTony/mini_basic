# mini_basic package

Phased extraction of the interpreter runtime into a proper Python package.
The CLI entry points are ``mini_basic.py`` (shim) and ``python -m mini_basic``.

**Backup:** see ``../backup/snapshot/`` for a frozen copy of the interpreter.


## Development Setup (Local Dev Tree vs Source Tree)

This tree supports independent development:

- **Local dev tree**: `Programming\mini_basic` (where you are working, lighter for focused/LLM sessions).
- **Source tree** (OneDrive): `C:\Users\Tony\mini_basic` (full tree with history, corpus, for distribution and remote checks).

### Git for Changes and History
Use git branches for independent fixes (see `DEVELOPMENT_GIT_USAGE.md` and `GIT_QUICKSTART.md`).
- Create branch: `git checkout -b fix/your-focus`
- Work with single focus, update status.
- Merge after user approval.
- This keeps clean version history instead of loose backup files.

### Status System
- `status.html` is the main monitoring page (updated by heartbeat).
- **Local**: for dev operation.
- **Source (OneDrive)**: for remote check (e.g. from phone/tablet via OneDrive sync).
- Heartbeat runs every minute via scheduled task (`scripts/ps1/register_progress_task.ps1`).
- To refresh: `python scripts\progress_heartbeat.py` (or direct `python -c "from utils.status_updater import StatusUpdater; StatusUpdater().update()" `).
- Note: Only status.html approach is used (phone/RSS remnants removed for simplicity).

### Periodic Sync Local Dev to Source
To keep source updated with local development (for full corpus, archives, remote status):
- Run `python scripts\sync_dev_to_source.ps1` (or the .ps1 version) periodically.
- Or manually copy key files and `status.html` to `C:\Users\Tony\mini_basic`.
- Then in source: `git add ... ; git commit` if tracking.

See `docs/git/INDEPENDENT_FIXES.md` for details on independent operation.

## Layout

Top-level organization (after recent cleanup):

- `mini_basic/` — the package (interpreter core)
- `examples/` — curated demos (bbc/, games/, graphics/, mini/, mits/ etc.)
- `basics/` — small standalone BASIC test programs
- `scripts/` — dev tools, runners, benchmarks
- `experiments/` — chat/ELIZA and throwaway AI experiments
- `lib/` — BBC libraries and fonts
- `test/`, `documentation/`, `utils/`, `backup/`

## Package Layout

| Module | Purpose |
|--------|---------|
| `__init__.py` | Public re-exports: types, config, runtime API |
| `__main__.py` | `python -m mini_basic` → delegates to `main()` |
| `runtime.py` | `BASICInterpreter`, REPL, CLI |
| `types.py` | `VarKind`, exceptions, dataclasses, control-flow frames |
| `config.py` | `InterpreterConfig`, `DEFAULT_CONFIG`, `SYSTEM_VAR_SPEC` |
| `constants.py` | Builtin name tables, CLI exit words, dialect reserved words |
| `expr/patterns.py` | Regex patterns for expressions and builtin calls |
| `expr/compile.py` | `CompiledExpr` — Python `compile()` cache for arithmetic |
| `expr/__init__.py` | Expression subpackage exports |
| `format/using.py` | MBASIC `PRINT USING` formatter |
| `format/__init__.py` | Re-exports `UsingFormatter` |
| `util/process.py` | `hard_exit()` for clean Ctrl+C shutdown on Windows |
| `util/__init__.py` | Utility exports |
| `repl/completion.py` | Tab completion for LOAD/SAVE/RUN/CD filenames |
| `repl/__init__.py` | REPL helper exports |

## Import guide

```python
from mini_basic import BASICInterpreter, main
from mini_basic.config import InterpreterConfig, DEFAULT_CONFIG
from mini_basic.format import UsingFormatter
from mini_basic.expr import CompiledExpr, patterns
```

## Running

```bash
python mini_basic.py --pygame examples/mini/bbc_graphics_demo.bas
python -m mini_basic --pygame examples/mini/bbc_graphics_demo.bas
```

## Tests

From project root:

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

