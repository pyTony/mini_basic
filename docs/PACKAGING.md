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
- `pip install "mini-basic[repl]"` → `pyreadline3` on Windows
- `pip install "mini-basic[all]"` → both

## Explicitly excluded from the wheel

| Path | Why |
|------|-----|
| `test/`, `tools/`, `utils/`, `scripts/` | Dev/agent tooling |
| `examples/`, `basics/`, `test/corpus/` | Demos and BBCSDL corpus (install separately or use text-archive dist) |
| `documentation/*.pdf`, large media | Not required to run the interpreter |
| `tools/python-embed/` | Bundled Python tree for offline installers |
| Agent status files, probes, `__pycache__` | Local noise |
| `mini_basic/diffcheck.py` | Removed — was a broken one-off (lived under `tools/` if kept) |
| Old text-archive installers | Separate distribution path (`tools/install.ps1` + parts) |

## Build & verify (local)

```powershell
cd C:\Users\Tony\mini_basic
python -m pip install -U build
python -m build
# Clean env smoke (example):
python -m venv .venv-pack
.\.venv-pack\Scripts\pip install dist\mini_basic-*.whl
.\.venv-pack\Scripts\mini-basic --version
.\.venv-pack\Scripts\python -m mini_basic -c "unused"  # if -c unsupported, use a temp .bas
```

Version is **PEP 440** (`1.0.0.dev0` while developing; tag `1.0.0` for release). Keep `mini_basic/version.py` in sync with root `pyproject.toml`.

## Not yet: upload

No `twine upload` until you choose a public project name and remote. This repo is local-first.
