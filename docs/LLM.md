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

## Language (short)

- Dialects: `mini` (default), `bbc`, `mits`, `commodore`, `tiny`.
- Case-on (default mini/bbc): **keywords uppercase**; names are case-sensitive. `CASE OFF` folds keywords.
- Use `MOD` for modulo. Bare `%` is an integer suffix, not modulo.
- `SIN` / `COS` / `TAN` use **radians** (`DEG` / `RAD` helpers exist).
- Regular product is text-only. Graphics (`--pygame`) is an optional extra, not required.

See [LANGUAGE_FEATURES_1.00.md](LANGUAGE_FEATURES_1.00.md) and [RELEASE_1.00.md](RELEASE_1.00.md).

## What is not in this public tree

Local agent/status files (`AGENT_POLICY.txt`, `CURRENT_TASK.txt`, `FEATURES_DONE.txt`, work logs, approval lists) stay on the developer machine. Do not recreate that pipeline here.
