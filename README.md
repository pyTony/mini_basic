# mini_basic

Python BASIC interpreter: multi-dialect (mini / bbc / mits / commodore / tiny),
REPL/CLI, and file I/O. Regular 1.00 is **text/console only**.

**CLI:** `python -m mini_basic` (guarantees which installed copy runs)  
(After a pip install: `mini-basic` / `minibasic`.)

Version: `mini_basic/version.py` (pre-release `1.0.0.dev0` until tagged).

**Docs (HTML):** open [`index.html`](index.html) at the clone root (pages are under [`docs/site/`](docs/site/index.html)) — [install](docs/site/install.html) · [public tree](docs/site/tree.html) · [language](docs/site/LANGUAGE_FEATURES_1.00.html)

**Install the interpreter from GitHub:**

```bash
python -m pip install "mini-basic[repl] @ git+https://github.com/pyTony/mini_basic.git"
mini-basic --version
```

Examples and the HTML handbook are in the git tree, not the pip wheel. Clone for those:

```bash
git clone https://github.com/pyTony/mini_basic.git
```

| On GitHub | What |
|-----------|------|
| [examples/](https://github.com/pyTony/mini_basic/tree/main/examples) | Curated BASIC programs ([README](https://github.com/pyTony/mini_basic/blob/main/examples/README.txt)) |
| [basics/](https://github.com/pyTony/mini_basic/tree/main/basics) | Small standalone `.bas` files |
| [docs/](https://github.com/pyTony/mini_basic/tree/main/docs) | Language / release notes |
| [GIT_QUICKSTART.md](https://github.com/pyTony/mini_basic/blob/main/GIT_QUICKSTART.md) | Developer git checklist |

Upstream (not this repo): [garyexplains/BASIC-M6502-CPORT](https://github.com/garyexplains/BASIC-M6502-CPORT) · [rtrussell/BBCSDL examples](https://github.com/rtrussell/BBCSDL/tree/master/examples)

## Quick start

```bash
python -m mini_basic examples/mini/hello_args.bas
python -m mini_basic --dialect mits examples/m6502-cport/01_hello.bas
python -m mini_basic basics/MB_COLOR.BAS
python -m mini_basic --dialect mits basics/ELIZA.BAS
python -m mini_basic --dialect bbc basics/BETH.BAS
python -m mini_basic --pygame --dialect bbc basics/mand_mode9_and.bas
python -m mini_basic --pygame --dialect bbc basics/jclock.bas
python -m mini_basic
```

```python
from mini_basic import BASICInterpreter, main
from mini_basic.config import InterpreterConfig

interp = BASICInterpreter(InterpreterConfig(dialect='bbc', display='none'))
```

## Showcase

Eight confirmed-working `examples/` programs picked to span graphics, fractals,
performance and language features. Run them all in order with:

```bash
python scripts/demo_reel.py          # run the whole reel
python scripts/demo_reel.py --list   # just print what's in it
python scripts/demo_reel.py wheel fern   # run only these entries
```

| | | |
|---|---|---|
| ![disco](docs/showcase/disco.png) **disco** — colour lightshow, grid redraw + palette cycling | ![illusion](docs/showcase/illusion.png) **illusion** — cafe-wall optical illusion: a dead-straight grid *looks* bent, purely from alternating corner wedges at each intersection | ![wheel](docs/showcase/wheel.png) **wheel** — spinning colour ring; `CASE`/`WHEN` dispatch, `CIRCLE` discs, `*REFRESH` |
| ![fern](docs/showcase/fern.png) **fern** — Barnsley fern fractal via chained `DRAW`/affine steps | **Mandel_ANSI** — Mandelbrot set in ANSI colour, console only, renders in well under a second (the interpreter's perf highlight) | ![bounce](docs/showcase/bounce.png) **bounce** — nested structs `Pos{x,y}`, whole-struct array copy, `+=` on struct members |
| **hanoi** — Towers of Hanoi, solved and animated recursively (interactive: enter a disc count, press SPACE) | ![soccerball](docs/showcase/soccerball.png) **soccerball** — spinning 3D ball via per-frame matrix rotation | |

`examples/` has ~30 more confirmed-working programs beyond this reel; see
[examples/README.txt](examples/README.txt) for the full tree.

## Dialects (short)

| Dialect | Notes |
|---------|--------|
| `mini` | Default; case-sensitive identifiers; keywords in any case (`for i = 1 to 3` works) |
| `bbc` | BBC-style; case-sensitive identifiers; keywords uppercase only |
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
| `documentation/feature_matrices/` | Capability matrices (generated) |
| `docs/BASIC_VARIANTS.md` | BASIC dialects / BBC family vs mini_basic (integrates matrices) |
| `docs/site/` | Browsable HTML handbook |
| `scripts/` | Dev tools (not collected as tests) |

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
python test/corpus_audit_probe.py
```

## Development notes

- **Git:** branch-per-focus; see `GIT_QUICKSTART.md` and `DEVELOPMENT_GIT_USAGE.md`.
- **LLM / contributors:** [`docs/LLM.md`](docs/LLM.md).

## Import map

```python
from mini_basic import BASICInterpreter, main
from mini_basic.config import InterpreterConfig, DEFAULT_CONFIG
from mini_basic.format import UsingFormatter
from mini_basic.expr import CompiledExpr, patterns
```

Package-level detail: `mini_basic/README.md`.
