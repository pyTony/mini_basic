# mini_basic documentation index

Browsable HTML (no extra tools): open [`../index.html`](../index.html) at the clone root, or [`site/index.html`](site/index.html) in this folder.

Markdown sources stay in this folder. `python scripts/build_user_docs.py` refreshes the generated pages under `site/` — that script, and the PDF/HTML manuals under `documentation/`, live on the [`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch.

---

## Start here

| Doc | What it is |
|-----|------------|
| [../README.md](../README.md) | Overview, quick start, pip install summary |
| [../HOWTO.md](../HOWTO.md) | Dev setup, modular runtime, common tasks |
| [RELEASE_1.00.md](RELEASE_1.00.md) | 1.00 release notes + tag checklist (user gate) |
| [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) | Language / graphics baseline for 1.00 ship |
| [PACKAGING.md](PACKAGING.md) | Wheel contents, extras (`display` / `repl` / `all`), build |
| [BASIC_VARIANTS.md](BASIC_VARIANTS.md) | Dialects and BBC family vs mini_basic |
| [LLM.md](LLM.md) | Short notes for people and LLMs |

## Language and implementation

| Doc | What it is |
|-----|------------|
| [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md#oscli-and-sys) | Supported language surface for 1.00 (includes OSCLI / SYS) |
| [PROGRAM_VS_TESTS.md](PROGRAM_VS_TESTS.md) | Approved programs vs pytest (user confirm when tests miss the look) |
| [BASIC_VARIANTS.md](BASIC_VARIANTS.md) | Dialect / BBC-family comparison |
| [../mini_basic/README.md](../mini_basic/README.md) | Package layout (import map, modules) |

Internal engineering notes (1.00 plan/VDU, BBC tokenize-vs-unglue, statement
dispatch map) live on the [`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch.

## Packaging and install

| Doc | What it is |
|-----|------------|
| [PACKAGING.md](PACKAGING.md) | pip / wheel / what is **not** in the package |
| [../HOWTO.md](../HOWTO.md) | Dev setup from a git clone, mixin regeneration |
| [../requirements-repl.txt](../requirements-repl.txt) | Windows REPL: pyreadline3 |
| [../requirements-display.txt](../requirements-display.txt) | Graphics: pygame-ce |

Editable install (this release tree):

```powershell
python -m pip install -U -e ".[all]"
```

## Git, development, feature matrices and examples

The git workflow checklist, feature-matrix generation, the PDF/HTML
manuals under `documentation/`, and the curated `examples/` tree all live
on the [`dev`](https://github.com/pyTony/mini_basic/tree/dev) branch —
clone `-b dev` to reach them.

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
