# mini_basic documentation index

One place to find project docs (mostly Markdown under `docs/` and the repo root).  
Source stays `.md` — not a permanent HTML tree.

## Browse in the browser (Windows)

Uses your existing helper (needs `npm install -g marked`):

```powershell
# From the mini_basic project root
Open-MdRendered.ps1 .\docs\INDEX.md

# Or open any page directly
Open-MdRendered.ps1 .\docs\PACKAGING.md
Open-MdRendered.ps1 .\docs\LANGUAGE_FEATURES_1.00.md
Open-MdRendered.ps1 .\README.md
```

`Open-MdRendered.ps1` lives in your user `bin` (e.g. `C:\Users\Tony\bin\`).  
It converts one file to a temp `.html` and opens the default browser.

**Note:** Links between pages work best in an editor Markdown preview (VS Code, Cursor) or by opening each file with `Open-MdRendered.ps1`. A temp HTML copy does not ship sibling `.md` files, so in-browser clicks on other docs may not resolve.

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
| [../GIT_QUICKSTART.md](../GIT_QUICKSTART.md) | Short continuous-git checklist |
| [../DEVELOPMENT_GIT_USAGE.md](../DEVELOPMENT_GIT_USAGE.md) | Fuller git / branch guide |
| [git/README.md](git/README.md) | `docs/git/` folder |
| [git/INDEPENDENT_FIXES.md](git/INDEPENDENT_FIXES.md) | Agent fix branches / independent fixes |
| [../DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md](../DEVELOPMENT_PIPELINE_AND_LLM_GUIDE.md) | Agent pipeline / LLM guide |
| [CLEAN_START.md](CLEAN_START.md) | Clean-start baseline notes |
| [../AGENT_POLICY.txt](../AGENT_POLICY.txt) | Agent operating rules (BEGIN/END, commits) |

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

## Session / history archives

| Doc | What it is |
|-----|------------|
| [SESSION_SUMMARIES_INDEX.md](SESSION_SUMMARIES_INDEX.md) | Index of archived session write-ups |
| [SESSION_CLAUDE_2026-08-09_LIST_SAVE_FORMATTER.md](SESSION_CLAUDE_2026-08-09_LIST_SAVE_FORMATTER.md) | LIST/SAVE formatter session |
| [SESSION_SUMMARY_archive_part1.md](SESSION_SUMMARY_archive_part1.md) | Archive part 1 |
| [SESSION_SUMMARY_archive_part2.md](SESSION_SUMMARY_archive_part2.md) | Archive part 2 |

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

*Open this file:* `Open-MdRendered.ps1 .\docs\INDEX.md`
