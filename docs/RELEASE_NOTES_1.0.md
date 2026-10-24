# mini_basic 1.0 — what's new

This is the first regular release of mini_basic: a multi-dialect BASIC
interpreter that runs classic BASIC programs, text or graphical, from a
single pip install or a git clone. It targets BBC BASIC (`bbc` dialect),
MITS/classic BASIC (`mits`/`commodore`/`tiny`), and its own modern superset
(`mini`).

For the full engineering scope (what's deliberately out, known
limitations) see
[LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md). This page is the
short, end-user version.

Install instructions live in `README.md` (repo root) and the handbook's
`docs/site/install.html` — not repeated here.

## Highlights

- **Five dialects** — `mini` (default, modern superset), `bbc` (BBCSDL/BB4W-style), `mits`, `commodore`, `tiny` (classic numbered BASIC).
- **Graphics** — `MODE`, `PLOT`/`DRAW`/`MOVE`, `CIRCLE`, `ELLIPSE`, `RECTANGLE`, palette/colour control, a pygame display window; see `showcase/` (`python showcase/demo_reel.py`).
- **Sound** — `SOUND` plays an approximate synthesized tone, `*PLAY "file"` plays a WAV sample, `*MUSIC "file"` streams a looping background track, all through real audio (`pygame.mixer`); see `showcase/breakout.bas` for all three together.
- **Procedures and structure** — `PROC`/`FN`, structs (`DIM name{a%,b$}`, whole-struct copy), whole-array operations, `ON ERROR`.
- **Libraries** — `LIBRARY`/`INSTALL` load another program's `DEF PROC`/`DEF FN` definitions into the running program without running its top-level code, matching real BBC BASIC semantics.
- **A small source editor** (`tools/editor.py`) — open/save/run, plus **Pretty (no numbers)** and **Renumber** buttons that delegate to the interpreter's own `LIST PRETTY` and `RENUMBER` logic.
- **REPL niceties** — numbered or unnumbered programs, `EDIT n` to edit one line in place or `EDIT` to drop into your system editor, tab completion, `HELP` (including `HELP CLI`).

## Updates after the initial 1.0 release

Later releases add an immediate-mode Listener (F5 / Shift+F5),
a wait-for-Esc Run toggle, and mini PRETTY comments written with apostrophes.
`EDIT NEW` opens a blank external-editor buffer and is also merged on `main`.
See the [editor guide](EDITOR.md) for usage and branch availability.

## Known limitations

- `ENVELOPE` is parsed but is a silent no-op — no ADSR shaping.
- Some real-time demos show flicker/jerky motion from frame-pacing, not a logic bug ([#12](https://github.com/pyTony/mini_basic/issues/12)).
- `CALL &FFF1` / `OSWORD 10` (cursor-position readback) isn't implemented ([#11](https://github.com/pyTony/mini_basic/issues/11)).

See [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) for the full list and rationale.

## Where to go next

| Doc | What it is |
|-----|------------|
| [PACKAGING.md](PACKAGING.md) | pip / wheel install options, extras |
| [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) | Full language/graphics baseline |
| `CHANGELOG.md` (repo root) | Per-PR history (`dev` branch) |
| `README.md` (repo root) | Quick start, dialects, layout |
