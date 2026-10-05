# mini_basic HOWTO

Preferred install (interpreter from GitHub):

```text
python -m pip install "mini-basic[repl] @ git+https://github.com/pyTony/mini_basic.git"
mini-basic --version
python -m mini_basic -c "PRINT 6*7"
```

Clone this (`main`) repo for `basics/` and the HTML handbook. Open `index.html` at the clone root (pages live in `docs/site/`). See `docs/site/install.html` and `docs/PACKAGING.md`.

## Modular runtime (what you get)

The interpreter is no longer a single giant `runtime.py` dump:

| Path | Role |
|------|------|
| `mini_basic/runtime.py` | Facade + REPL/CLI/`main` |
| `mini_basic/runtime_parts/` | Mixin modules (core, program, expr, defs, execution, io, graphics, dialect) + helpers |

Public import is unchanged: `from mini_basic import BASICInterpreter, main`.

## Development setup

This `main` branch is the lean release tree. The full dev tree
(`test/`, `tools/`, `scripts/`, `examples/`, `documentation/`, and the git
workflow docs) lives on the
[`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch:

```powershell
git clone -b dev https://github.com/pyTony/mini_basic.git
cd mini_basic
python -m pip install -e ".[repl]"
python -m mini_basic --help
python -m pytest -q -m "phase1 and not slow" --timeout=45
```

Optional extras:

```powershell
pip install -r requirements-repl.txt
pip install -r requirements-display.txt
```

## Regenerating mixins (developers)

If you edit a monorepo snapshot of `runtime.py` and want to re-emit the `runtime_parts/` mixins, from a `dev` checkout:

```powershell
python tools/split_runtime_mixins.py
python -m pytest -q -m "phase1 and not slow" --timeout=45
```

See `mini_basic/RUNTIME_MODULARIZATION_STATUS.md`.

## Requirements

- Python 3.10+
- PowerShell (Windows helper scripts under `tools/`, `scripts/ps1/` on the `dev` branch) — optional, not required to run or develop the interpreter

## Common tasks

| Task | Command |
|------|---------|
| Run a program | `python -m mini_basic basics/MB_COLOR.BAS` |
| Run the test suite (on `dev`) | `python -m pytest -q -m "phase1 and not slow" --timeout=45` |
| Split runtime mixins (on `dev`) | `python tools/split_runtime_mixins.py` |

## Troubleshooting

- Missing graphics → `pip install -r requirements-display.txt` (or `pip install "mini-basic[display]"`).
- `mini-basic`/`minibasic` not found after `pip install` → open a **new** shell so `PATH` picks up the console scripts, or confirm the Python Scripts/bin directory is on `PATH`.

For language notes see `docs/LLM.md`.
For git rules see `GIT_QUICKSTART.md` on the [`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch.
