# mini_basic documentation index

Browsable HTML (no extra tools): open [`site/index.html`](site/index.html) in a browser after cloning the repo.

Markdown sources stay in this folder; `python scripts/build_user_docs.py` refreshes the generated pages under `site/`.

Already-HTML manuals open without `marked`:

```powershell
Start-Process .\documentation\MINIBASIC_BBC_BASIC_Manual.html
Start-Process .\documentation\BBC_BASIC_Manual.html
```

---

## Start here

| Doc | What it is |
|-----|------------|
| [../README.md](../README.md) | Overview, quick start, pip install summary |
| [../HOWTO.md](../HOWTO.md) | Install archives, text parts, common tasks |
| [RELEASE_1.00.md](RELEASE_1.00.md) | 1.00 release notes + tag checklist (user gate) |
| [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) | Language / graphics baseline for 1.00 ship |
| [PACKAGING.md](PACKAGING.md) | Wheel contents, extras (`display` / `repl` / `all`), build |
| [BASIC_VARIANTS.md](BASIC_VARIANTS.md) | Dialects and BBC family vs mini_basic |
| [LLM.md](LLM.md) | Short notes for people and LLMs |

## Language and implementation

| Doc | What it is |
|-----|------------|
| [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) | Supported language surface for 1.00 |
| [PLAN_1.00_AND_VDU.md](PLAN_1.00_AND_VDU.md) | 1.00 plan and VDU notes |
| [BASIC_VARIANTS.md](BASIC_VARIANTS.md) | Dialect / BBC-family comparison (links matrices) |
| [BBC_TOKENIZE_VS_UNGLUE.md](BBC_TOKENIZE_VS_UNGLUE.md) | Real BBC tokens vs mini eval-time unglue |
| [../mini_basic/README.md](../mini_basic/README.md) | Package layout (import map, modules) |

## Packaging and install

| Doc | What it is |
|-----|------------|
| [PACKAGING.md](PACKAGING.md) | pip / wheel / what is **not** in the package |
| [../HOWTO.md](../HOWTO.md) | Text-archive `install.ps1` / `dev_install.ps1` |
| [../requirements-repl.txt](../requirements-repl.txt) | Windows REPL: pyreadline3 |
| [../requirements-display.txt](../requirements-display.txt) | Graphics: pygame-ce |

Editable install (dev tree):

```powershell
python -m pip install -U -e ".[all]"
# or embed Python:  .\tools\python-embed\python.exe -m pip install -U -e ".[all]"
```

## Git and development

| Doc | What it is |
|-----|------------|
| [../GIT_QUICKSTART.md](../GIT_QUICKSTART.md) | Short git checklist |
| [../DEVELOPMENT_GIT_USAGE.md](../DEVELOPMENT_GIT_USAGE.md) | Fuller git / branch guide |
| [git/README.md](git/README.md) | `docs/git/` folder |
| [LLM.md](LLM.md) | Language / test notes for LLMs |

## Feature matrices and manuals (`documentation/`)

Generated / reference material (mostly not Markdown):

| Path | What it is |
|------|------------|
| [../documentation/feature_matrices/](../documentation/feature_matrices/) | Capability grids (`.txt`; open in editor) |
| [../documentation/feature_matrices/ALL_MATRICES.txt](../documentation/feature_matrices/ALL_MATRICES.txt) | Combined dump |
| [../documentation/MINIBASIC_BBC_BASIC_Manual.html](../documentation/MINIBASIC_BBC_BASIC_Manual.html) | Built mini_basic-oriented HTML manual |
| [../documentation/BBC_BASIC_Manual.html](../documentation/BBC_BASIC_Manual.html) | BBC reference HTML |
| [../documentation/BBC BASIC Reference Manual.pdf](../documentation/BBC%20BASIC%20Reference%20Manual.pdf) | BBC PDF (if present) |

Regenerate matrices from the package:

```bash
python -m mini_basic.features
```

## Examples (READMEs)

Git tree (not in the pip wheel): [github.com/pyTony/mini_basic](https://github.com/pyTony/mini_basic) · [examples/](https://github.com/pyTony/mini_basic/tree/main/examples)

| Doc | What it is |
|-----|------------|
| [../examples/README.txt](../examples/README.txt) | Examples tree map |
| [../examples/vdu/README.md](../examples/vdu/README.md) | VDU demos |
| [../examples/teletext/README.md](../examples/teletext/README.md) | Teletext samples |
| [../examples/m6502-cport/README.md](../examples/m6502-cport/README.md) | M6502 C-port tutorials ([upstream](https://github.com/garyexplains/BASIC-M6502-CPORT)) |

## Runtime internals (package)

| Doc | What it is |
|-----|------------|
| [../mini_basic/RUNTIME_MODULARIZATION_STATUS.md](../mini_basic/RUNTIME_MODULARIZATION_STATUS.md) | Mixin split status |
| [../mini_basic/RUNTIME_VERSION_HISTORY.md](../mini_basic/RUNTIME_VERSION_HISTORY.md) | Runtime version notes |

## In-REPL help (no Markdown)

At the `>` prompt:

```text
HELP
HELP PROGRAM
HELP REPL
HELP FUNCTIONS
HELP DEBUG
MATRIX
```

---

*HTML home:* [`site/index.html`](site/index.html)
