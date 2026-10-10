# Notes for people and LLMs

mini_basic is a **multi-dialect BASIC interpreter** (console / text). It is not full BBCSDL, RISC OS, or a packaging toolkit.

## Run

```text
python -m mini_basic file.bas
python -m mini_basic --dialect mits examples/m6502-cport/01_hello.bas
python -m mini_basic --help
```

Tests from the project root:

```text
python -m pytest -q -m "phase1 and not slow" --timeout=45
```

## Architecture at a glance

![mini_basic architecture: dialect parsing, runtime_parts mixins, text and pygame backends](img/architecture.jpg)

*Overview illustration (generated with Gemini Notebook). Read it for the shape, not the details: the text inside the terminal panel is illustrative, not real output, and the module ring omits `strplan` (cached string expressions). For the real map of where each statement is handled, see [DISPATCH_MAP.md](DISPATCH_MAP.md).*

## Language (short)

- Dialects: `mini` (default), `bbc`, `mits`, `commodore`, `tiny`.
- Case-on (default mini/bbc): names are case-sensitive. **bbc** keywords are uppercase only; **mini** accepts any keyword case (`for i = 1 to 3` is stored as `FOR i = 1 TO 3`). `CASE OFF` folds keywords.
- Use `MOD` for modulo. Bare `%` is an integer suffix, not modulo.
- `SIN` / `COS` / `TAN` use **radians** (`DEG` / `RAD` helpers exist).
- Regular product is text-only. Graphics (`--pygame`) is an optional extra, not required.

See [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) and [RELEASE_1.00.md](RELEASE_1.00.md).
