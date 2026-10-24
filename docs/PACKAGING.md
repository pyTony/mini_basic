# Packaging (PyPI / pip) — what ships and what does not

## Included in the wheel (`pip install mini-basic`)

Only the **importable interpreter package** under `mini_basic/`:

| Area | Modules (examples) |
|------|--------------------|
| Entry | `__init__`, `__main__`, `runtime`, `version`, `config` |
| Language | `runtime_parts/*`, `expr/*`, `type_system`, `constants`, `dialect_hint` |
| BBC graphics | `display`, `bbc_graphics`, `bbc_modes`, `bbc_font`, `bbc_detokenize` |
| Optional helpers | `features/*` (matrices text generation), `format/*`, `repl/*`, `util/*` |
| CLI | console scripts `mini-basic`, `minibasic`, `mini_basic` → `mini_basic:main` |

**Optional extras** (not hard dependencies):

- `pip install "mini-basic[display]"` → `pygame-ce` (MODE/PLOT windows)
- `pip install "mini-basic[accel]"` → `numpy` (uint8 framebuffer / fast present)
- `pip install "mini-basic[repl]"` → `pyreadline3` on Windows
- `pip install "mini-basic[all]"` → display + accel + repl

## Explicitly excluded from the wheel

| Path | Why |
|------|-----|
| `basics/`, `showcase/` | Demo programs — get from [git](https://github.com/pyTony/mini_basic/tree/main), not the wheel |
| `test/`, `scripts/`, `tools/`, `examples/`, `documentation/` | Never part of the wheel; `test/` and `scripts/` live only on the [`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch |
| `__pycache__` | Build leftover |
| `mini_basic/diffcheck.py` | Removed — was a broken one-off |

## Install from GitHub (supported)

```powershell
python -m pip install "mini-basic @ git+https://github.com/pyTony/mini_basic.git"
python -m pip install "mini-basic[repl] @ git+https://github.com/pyTony/mini_basic.git"
mini-basic --version
python -m mini_basic -c "PRINT 6*7"
```

That installs the interpreter only. For `basics/` and `docs/site/`:

```powershell
git clone https://github.com/pyTony/mini_basic.git
cd mini_basic
python -m pip install -e ".[repl]"
```

For the development tree (`test/`, `scripts/`), clone the [`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch instead.

## Build a wheel (local checkout)

```powershell
python -m pip install -U build
python -m build
python -m venv .venv-pack
.\.venv-pack\Scripts\pip install dist\mini_basic-*.whl
.\.venv-pack\Scripts\mini-basic --version
.\.venv-pack\Scripts\python -m mini_basic -c "PRINT 6*7"
```

Version is **PEP 440** (`1.0.0.dev0` while developing; tag `1.0.0` for release). Keep `mini_basic/version.py` in sync with root `pyproject.toml`.

Public source: [github.com/pyTony/mini_basic](https://github.com/pyTony/mini_basic). No PyPI upload until you choose to publish.
