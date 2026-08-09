# Microsoft BASIC (M6502) C-port examples

Numbered tutorial programs and small apps from:

**[garyexplains/BASIC-M6502-CPORT](https://github.com/garyexplains/BASIC-M6502-CPORT)**  
(`cport/examples/` — hosted C port of Microsoft BASIC for 6502, Apple II config)

Upstream license: MIT (see `LICENSE.upstream`).

These are classic **numbered-line** BASIC demos (print, FOR/NEXT, GOSUB, arrays,
DATA/READ, DEF FN, strings, simple file I/O). They fit mini_basic’s **mits**
dialect better than **bbc**/pygame demos.

## Run with mini_basic

```powershell
# non-interactive tutorials (01–48)
python -m mini_basic -q --dialect mits examples\m6502-cport\01_hello.bas
python -m mini_basic -q --dialect mits examples\m6502-cport\09_for_loop.bas
python -m mini_basic -q --dialect mits examples\m6502-cport\40_bubble_sort.bas

# interactive (pipe answers)
@("Ada","30") | python -m mini_basic -q --dialect mits examples\m6502-cport\49_input_greeting.bas

# adventure (cwd matters for rooms.txt / objects.txt)
cd examples\m6502-cport\adv
python -m mini_basic -q --dialect mits adventure.bas
```

`commodore` or `tiny` may work for many of the same files; prefer **mits**.

## Layout

| Path | Contents |
|------|----------|
| `01_*.bas` … `60_*.bas` | Tutorial ladder (syntax → algorithms → host file I/O) |
| `apps/` | hangman, calendar, caesar, number guessing, … |
| `adv/` | Editable text adventure + data files |

## Notes / limits (mini_basic vs C-port MS BASIC)

Most of **01–48** run under `--dialect mits`. Known gaps when using mini_basic:

| Examples | Issue |
|----------|--------|
| `08_goto_counter` | MS allows `N=N+1` before `N` is set; mini_basic needs `N=0` first |
| `04_integer_variables` | `%` expression edge cases may still trip the integer path |
| `21`–`22` DEF FN | MS form `DEF FN S(X)=…` (space after FN); mini expects glued `DEF FNS(X)=…` |
| `29`–`30` | `POKE` / `WAIT` not implemented |
| `51`–`60` | Host `OPEN`/`PRINT#`/`GET#`/`CMD` spellings from the C port; mini is closer to BBC file I/O |
| Interactive `49`–`50`, `apps/`, `adv/` | Need keyboard or piped answers |

These files remain useful as a classic MS BASIC tutorial set and as dialect-parity targets.

Full index of the 60 programs: see the table in this directory’s upstream `README.md` (from C-port).
