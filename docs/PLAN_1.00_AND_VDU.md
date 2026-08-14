# VDU status and mini_basic 1.00 finish plan

**Goal:** Finish a honest **1.00** release without burning full-day agent tokens on unbounded parity.

**Rules:** One focus per session · fixed acceptance criteria · corpus-driven · no drive-by refactors.

---

## 1. VDU implementation status (as of 2026-07)

**Code:** [`mini_basic/runtime_parts/execution.py`](../mini_basic/runtime_parts/execution.py) — `_execute_vdu`  
**Parse:** [`mini_basic/runtime_parts/program.py`](../mini_basic/runtime_parts/program.py) — `_parse_vdu_operands` (`,` + `;` word split OK)

### Implemented today

| Code | Meaning | Notes |
|------|---------|--------|
| 4 / 5 | Text / graphics PRINT | `set_graphics_print_mode` |
| 12 | CLS | `_clear_screen` |
| 16 | CLG | clear graphics |
| 18,m,c | GCOL | |
| 25,k,x;y; | PLOT | |
| 29,x;y; | ORIGIN | |
| 31,x,y | Cursor position | |
| 23,1,0\|1 | Cursor hide/show | ANSI |
| 23,22,w;h;… | Custom graphics mode | BBCSDL |
| 32–126 | Printable | |
| 136 / 137 | Flash on/off | |
| ≥128 MODE 7 | Teletext-ish write | partial |

**Also (not via `VDU` statement):** `COLOUR` keyword, PRINT-path VDU 17 pairs (hanoi wrap), `@vdu%!n` stubs.

### Confirmed missing in `_execute_vdu`

| Code | Meaning | Priority for 1.00 |
|------|---------|-------------------|
| **17** | Text colour (COLOUR) | **P0** — bug if programs use `VDU 17,n` |
| **20** | Reset colours | **P0** |
| **26** | Reset viewports | **P0** (even soft) |
| **30** | Cursor home | **P0** |
| **28** | Text viewport | **P1** |
| **24** | Graphics viewport | **P1** |
| **7** | Bell | **P1** (no-op or `\a`) |
| **8–11, 13** | Cursor left/right/down/up, CR | **P1** |
| **23,0** and other 23,* | BBCSDL/RISC OS extras | **P1** stub: consume, no error |

### Corpus demand (lead code after `VDU`, BBCSDL tree)

| Lead | Count | Gap |
|------|------:|-----|
| 23 | 248 | Only 23,1 + 23,22 real; 23,0 ×96 need stub |
| 28 | 32 | missing |
| 24 | 28 | missing |
| 31 | 26 | OK |
| 5 / 26 | 21 | 5 OK; 26 missing |
| 20 | 13 | missing |
| 30 | 12 | missing |

**Not 1.00:** full teletext SAA5050, VDU 23 pattern defs, WIMP, Box2D, full ENVELOPE (see `features/deferred.py`).

---

## 2. What 1.00 means (scope lock)

1. **Dialects** mini / mits / commodore / tiny / bbc — control flow, files, INPUT/PRINT, ON ERROR.
2. **BBC graphics tier A** — MODE, GCOL, MOVE/DRAW/PLOT, CIRCLE, COLOUR, *REFRESH, ORIGIN + VDU Phase A–C below.
3. **Corpus** — every FAIL is **OK** or **documented deferred** ([`CORPUS_AUDIT.txt`](../CORPUS_AUDIT.txt): welcome, piechart, polly, poem).
4. **Ship hygiene** — text-only no auto-pygame, terminal Ctrl+C/ESC, Russell detokenize CASE, version string, short release notes.
5. **Non-goals** — full BBCSDL tools/physics/OpenGL/teletext fidelity.

---

## 3. Token-efficient process

| Rule | Practice |
|------|----------|
| One focus | One VDU family **or** one corpus program — never both |
| Fixed exit | 1 pytest target green → **stop** |
| Small diff | Prefer only `_execute_vdu` + one test file |
| Short probes | `pytest -q path::Test` not long animations |
| Session budget | ≤3 code regions + ≤2 test files per chat |
| Bookkeeping | Keep the public docs in sync; local notes stay local |

---

## 4. Phases (ROI order)

### Phase A — VDU must-have (~3–5 short sessions)

1. **VDU 17** — same as one-arg COLOUR (`set_colour` / text_fg/bg).
2. **VDU 20** — reset default text colours (and soft palette if free).
3. **VDU 30, 8–11, 13** — home / left / right / down / up / CR.
4. **VDU 7** — bell no-op or `\a`.
5. **VDU 26** — reset viewports to full (even if clip is soft).

### Phase B — Viewports (~0–2 sessions)

- **VDU 28** text viewport, **VDU 24** graphics viewport.
- If hard: **stub** (accept args, no clip) for 1.00; full clip only if a user-approved demo needs it.

### Phase C — VDU 23 stubs (1 session)

- `VDU 23,0,…` and unknown `23,n`: consume operands, no error.
- Keep `23,1` and `23,22`.

### Phase D — Corpus FAIL (one program per session)

| Program | 1.00 choice |
|---------|-------------|
| welcome.txt | Fix or defer (ENVELOPE stub) |
| piechart.txt | **Defer** unless trivial |
| polly.txt | **Defer** (sound) |
| poem.txt | Timeout tweak or defer |

### Phase E — Ship 1.00 (1 session)

- `--version` / version constant  
- `RELEASE_1.00.md` or README: dialects, VDU table, env vars, deferred  
- Green: phase1 pytest + VDU tests + session_display  
- Freeze the 1.00 language baseline in `LANGUAGE_FEATURES_1.00.md`

---

## 5. Immediate next session

**Focus: VDU 17 only**

- `_execute_vdu`: `code == 17` + next byte → COLOUR path  
- Test: `VDU 17,1` sets fg  
- Do **not** start viewports or welcome in the same session  

---

## 6. Checklist: “VDU done for 1.00”

- [x] VDU 4,5,12,16,17,18,20,25,26,29,30,31,23.1,23.22 tested  
- [x] VDU 7,8–11,13 work or documented  
- [x] Unknown VDU 23,* does not crash  
- [x] VDU 24 / 28 store (+ text cursor clamp); full pixel clip optional later  
- [ ] Corpus FAIL empty or explicit deferred  
- [ ] Release notes list VDU coverage + non-goals  

---

## 7. Tracking

Record finished VDU work in tests and `LANGUAGE_FEATURES_1.00.md`. Local checklists stay off GitHub.
