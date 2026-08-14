# mini_basic HOWTO

This guide covers setup for both **end users** and **developers**.

See the main `README.md` (in this folder or inside the tree) for a quick overview and usage examples.

## Modular runtime (what you get)

The interpreter is no longer a single giant `runtime.py` dump:

| Path | Role |
|------|------|
| `mini_basic/runtime.py` | Facade + REPL/CLI/`main` |
| `mini_basic/runtime_parts/` | Mixin modules (core, program, expr, defs, execution, io, graphics, dialect) + helpers |
| `mini_basic.py` / `mb.py` | Entry shims |

Public import is unchanged: `from mini_basic import BASICInterpreter, main`.

## End-User Installation

There are two end-user archive kinds:

| Kind | Parts | Contents |
|------|--------|----------|
| **cli** (smallest, **no pixel graphics**) | `mini_basic_text_cli_part*.txt` | Interpreter + `basics/` + CLI samples (`examples/mini`, `mits`, `museum`, `bbc`). Omits `bbc_font` / `bbc_graphics`, games trees, and `requirements-display.txt`. Display: **terminal** / **none** only (not pygame). Ships `CLI_ONLY.txt`. |
| **dist** (full samples) | `mini_basic_text_dist_part*.txt` | Everything in cli **plus** full `examples/` and pygame requirements file. |

You need:

- `install.ps1`
- `README.md` (optional but recommended)
- `archive/` (or `archives/`, `dist/`) containing **one** kind of parts

### CLI-only layout (recommended for terminal / servers)

```
install.ps1
README.md
archive/
    mini_basic_text_cli_part01.txt
    mini_basic_text_cli_part02.txt
    ...
```

```powershell
.\install.ps1 -ArchiveKind cli
# or, if only cli parts are present:
.\install.ps1
```

### Full dist layout

```
install.ps1
README.md
archive/
    mini_basic_text_dist_part01.txt
    ...
```

```powershell
.\install.ps1 -ArchiveKind dist
# auto (default): prefers dist if both kinds exist, else cli, else legacy
.\install.ps1
```

The installer discovers parts in `archive/`, `archives/`, `dist/`, or next to the script.
Legacy names `mini_basic_text_part*.txt` are still accepted as a fallback (treated as dist).

### Steps

1. Open PowerShell and `cd` to the folder that contains `install.ps1`.
2. Run `.\install.ps1` (optionally `-ArchiveKind cli` or `dist`).
   - Creates a `mini_basic\` subfolder (the project).
   - Verifies `mini_basic/runtime_parts/*` and runs a Python import smoke test when possible.
   - Sets the `MINIBASIC_DIR` user environment variable.
   - Creates launchers (`mini_basic` / `minibasic`) in `~/bin`.
   - Initializes git in the target (first time).

3. Close the PowerShell window and open a **fresh** one (important for env var + PATH).

4. Test:
   ```powershell
   mini_basic basics\fact.bas
   mini_basic --help
   mini_basic --display none examples\mini\hello_args.bas
   ```

### Uninstall

```powershell
.\install.ps1 -Uninstall
```

## Development Setup (Full Dev Tree)

### Option A: Use the source tree directly

The repository **is already** the full dev tree (`mini_basic/`, `test/`, `tools/`, …).

```powershell
python -m mini_basic --help
python -m pytest -q -m "phase1 and not slow" --timeout=45
```

### Option B: Text-based dev installation (reproducible)

Use **`dev_install.ps1` + standalone dev parts** (no separate core archive).

`create_text_archive.py --mode dev` builds a **complete** tree: everything in dist **plus** `test/`, `scripts/`, `tools/`, `utils/`, `docs/`, etc.

**Files needed:**

- `dev_install.ps1`
- Parts in `archive/` or `dist/`:
  - `mini_basic_text_dev_part01.txt`
  - `mini_basic_text_dev_part02.txt`
  - …

Example layout:

```
dev_install.ps1
archive/
    mini_basic_text_dev_part01.txt
    ...
```

```powershell
.\dev_install.ps1
# or
.\dev_install.ps1 -TargetDir "C:\temp\my_dev_tree"
```

Default target: `mini_basic_dev` next to the script.

After install:

```powershell
cd mini_basic_dev
python -m mini_basic --help
python -m pytest -q -m "phase1 and not slow" --timeout=45
```

## Generate / reconstruct text archives

From a full source tree:

```powershell
# Command-line only (smallest end-user package)
python tools/create_text_archive.py --mode cli --outdir dist

# Full curated samples (includes games/graphics trees)
python tools/create_text_archive.py --mode dist --outdir dist

# Full dev parts
python tools/create_text_archive.py --mode dev --outdir dist

# dist + dev
python tools/create_text_archive.py --mode both --outdir dist

# cli + dist + dev
python tools/create_text_archive.py --mode all --outdir dist
```

Manual reconstruct (Python):

```powershell
python tools/reconstruct_from_text.py dist/mini_basic_text_cli_part*.txt -o my_cli --verify
python tools/reconstruct_from_text.py dist/mini_basic_text_dist_part*.txt -o my_tree --verify
python tools/reconstruct_from_text.py dist/mini_basic_text_dev_part*.txt -o my_dev --verify
```

`--verify` checks that the modular package (`runtime.py` + `runtime_parts/`) is present and importable.

### What the **cli** archive includes

- Full interpreter (runtime facade + `runtime_parts/` mixins) for text CLI use
- `display.py` with **TerminalDisplay** / **NullDisplay** only usable backends
- `basics/` plus CLI-oriented examples: `examples/mini`, `mits`, `museum`, `bbc`
- `documentation/` feature matrices (except the graphics matrix)
- Root shims, HOWTO, README/FEATURES, `requirements-repl.txt`, `install.ps1`, **`CLI_ONLY.txt`**
- Archive helpers: `create_text_archive.py`, `reconstruct_from_text.py`, `install.ps1`

### What the **cli** archive excludes (no graphics)

- `mini_basic/bbc_font.py`, `mini_basic/bbc_graphics.py` (pygame/MOS pixel stack)
- entire `mini_basic/features/` package (matrix tooling)
- Graphics demos (`bbc_graphics_demo.bas`, `sprites_demo.bas`)
- `examples/games|graphics|physics|sounds|tools|general`
- `requirements-display.txt`, `dev_install.ps1`
- `--display pygame` raises ImportError (install full **dist** package for graphics)

### What the **dist** archive includes

- Everything needed for a full curated tree (all of `examples/`, display requirements)
- `install.ps1` / `dev_install.ps1` at tree root **and** under `tools/`
- Extra helpers (`split_runtime_mixins.py`, …)

### What is never archived

- `backup/` (monorepo dumps, obsolete stubs)
- `dist/` prior output (avoids nesting old parts)
- `__pycache__` / caches
- Obsolete package-root dumps such as `runtime_FROM_GIT_HEAD.py` if reintroduced

## Regenerating mixins (developers)

If you edit a monorepo snapshot and want to re-emit mixins:

```powershell
# monorepo must be the full BASICInterpreter source (~500KB+), not the facade
Copy-Item backup\runtime_monolith.py mini_basic\runtime.py -Force
# edit… then:
python tools/split_runtime_mixins.py
python -m pytest -q -m "phase1 and not slow" --timeout=45
```

See `mini_basic/RUNTIME_MODULARIZATION_STATUS.md`.

## Requirements

- Windows 10+
- PowerShell 5.1 or 7+
- Python 3 (on PATH)

Optional:

```powershell
pip install -r requirements-repl.txt
pip install -r requirements-display.txt
```

## Common tasks

| Task | Command |
|------|---------|
| Build CLI-only archive | `python tools/create_text_archive.py --mode cli --outdir dist` |
| Build dist+dev archives | `python tools/create_text_archive.py --mode both --outdir dist` |
| Build all three kinds | `python tools/create_text_archive.py --mode all --outdir dist` |
| Reconstruct CLI + verify | `python tools/reconstruct_from_text.py dist/mini_basic_text_cli_part*.txt -o t --verify` |
| End-user install (CLI) | `.\install.ps1 -ArchiveKind cli` |
| End-user install (full) | `.\install.ps1 -ArchiveKind dist` |
| Dev install | `.\dev_install.ps1` |
| Split runtime mixins | `python tools/split_runtime_mixins.py` |

## Troubleshooting

- Commands not found after install → open a **new** shell.
- Install aborts with “missing modular runtime files” → regenerate archives with the current `create_text_archive.py` (old parts may predate `runtime_parts/`).
- Wrong tree active → set `MINIBASIC_DIR` to the reconstructed project root.
- Missing graphics → `pip install -r requirements-display.txt`.

For language notes see `docs/LLM.md`.  
For git rules see `GIT_QUICKSTART.md`.
