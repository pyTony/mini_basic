# mini_basic package

Interpreter package for multi-dialect BASIC (mini / bbc / mits / commodore / tiny).

CLI: `python -m mini_basic` (see top-level `README.md` for project-wide docs).

## Layout

| Module / path | Purpose |
|---------------|---------|
| `__init__.py` | Public re-exports |
| `__main__.py` | `python -m mini_basic` → `main()` |
| `runtime.py` | Facade: `BASICInterpreter` (mixin composition), REPL, CLI |
| `runtime_parts/` | Mixins: core, program, expr, defs, execution, io, graphics, dialect, helpers |
| `type_system.py` | `VarKind`, `BasicRuntimeError`, control-flow frames |
| `config.py` | `InterpreterConfig`, defaults |
| `constants.py` | Builtin tables, dialect reserved words |
| `display.py` | Terminal / pygame / null displays |
| `expr/` | Compiled expression cache + patterns |
| `format/` | `PRINT USING`, save-case helpers |
| `repl/` | Completion, help browser, Windows input |
| `features/` | Feature-matrix data for docs / `python -m mini_basic.features` |
| `bbc_*.py` | BBC modes, font, graphics helpers, detokenize, corpus scan |

## Import guide

```python
from mini_basic import BASICInterpreter, main
from mini_basic.config import InterpreterConfig, DEFAULT_CONFIG
from mini_basic.format import UsingFormatter
from mini_basic.expr import CompiledExpr, patterns
```

## Running

```bash
python -m mini_basic examples/mini/hello_args.bas
python -m mini_basic --pygame examples/mini/bbc_graphics_demo.bas
```

## Tests

From **project root** (not this directory):

```bash
python -m pytest -q test/test_mini_basic.py --timeout=30
python -m pytest -q -m "phase1 and not slow" --timeout=20
```
