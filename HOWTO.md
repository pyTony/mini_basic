# mini_basic HOWTO

## Microsoft numeric PRINT spacing

Use `--dialect mits` for Microsoft/MITS BASIC or `--dialect commodore` for
Commodore BASIC. Numeric PRINT items reserve a leading sign space for zero and
positive values, and end with a space: `PRINT "[";1;0;-2;"]"` prints
`[ 1  0 -2 ]`. Semicolons suppress additional separators, not these numeric
spaces. Commas retain the configured print zones. `STR$` and `PRINT USING`
keep their own formatting. The default `mini` and explicit `bbc` modes retain
their existing output behavior.

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

## Simple source editor (developers, `dev` branch)

`tools/editor.py` is a minimal tkinter editor for `.bas`/`.bbc` source:
open/save, mini_basic-aware syntax highlighting (keywords, `PROC`/`ENDPROC`,
`*`-commands, line numbers, dialect hint comments), and a toolbar with:

- **Run** — launches the real interpreter as a subprocess (`python -m
  mini_basic <file>`, with the toolbar's dialect dropdown and `--pygame`
  checkbox). It does not reimplement any display — pygame programs still
  open their own window and console programs still use the normal
  terminal.
- **Pretty (no numbers)** — reformats the buffer the same way `SAVE
  PRETTY` / `LIST PRETTY` do in the REPL (delegates to the interpreter).
- **Renumber** — renumbers the program 10, 20, 30, … and fixes up
  `GOTO`/`GOSUB`/etc. targets (delegates to the interpreter's own
  `RENUMBER`/`REN` logic).

```powershell
python tools/editor.py [file.bas]
```

Out of scope for now: an in-editor REPL or replacing the pygame/terminal
output paths — see `test/test_editor_smoke.py` for the current coverage.

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
