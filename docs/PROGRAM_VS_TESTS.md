# Approved programs vs pytest

Pytest locks **language fragments** (and a few one-frame kernels). It does not replace
running the program. If a program’s distinctive use is only visible when you play it,
that program stays **user confirmation only**.

Sources: corpus `.txt` listings (tokenized `.bbc` files are binary).

## What each program uniquely uses

| Program | Distinctive use (not just FOR/MODE) | Regular pytest | User confirmation |
|---------|--------------------------------------|----------------|-------------------|
| **squares** | `VDU 23,22` user mode; nested int FOR; `(X EOR Y) AND 255` kernel | Loads `squares.bbc`; pixel formula + &lt;5s | Look of the full munching square |
| **soccerball** | `CIRCLE FILL`, `PLOT 85` facets, `COLOUR` sky vs pixels | Loads `.bas`; dirty-rect / rim math | Spinning ball, FPS, second RUN |
| **wheel** | `CASE`/`WHEN`, `CIRCLE` discs, `*REFRESH` | Loads `wheel.bbc` one frame; detokenize | Colour ring / motion |
| **piechart** | `Colour&() OR=`, compact IF, `PLOT 85` sectors, `OSCLI GSAVE` | Loads corpus + glue/GSAVE tests | Label/sky look |
| **Clock** (`Clock.bas`) | `GCOL 3` XOR hands, digital `PRINT` on plot | Loads `Clock.bas`; XOR erase | Live clock face |
| **welcome** | `ENVELOPE`/`SOUND` stubs, `VDU 23` glyphs, glued `AND`/`DIV`, `REPEATUNTIL TIME` | Snippets (`test_welcome_*`) | Full zap / letter animation |
| **saucer** | Float nested `FOR` disc + `GCOL` hidden-line `PLOT` | Control-flow + `NOTX` load smoke | Shape OK (2026-08-15); draw still slow |
| **jclock** | `WHEN` colon, `SINRADT`, live `MOUSE`/`TIME$` | WHEN / `SINRAD` snippets | Hands follow the mouse |
| **flier** | 400+ lines, `_BOX`/`_LINE`, `DRAW`/`OSCLI` ship | Leading-underscore names only | Rotating ship |
| **filters** | FIR / array slice waveforms, `ORIGIN` | `Original` vs `ORIGIN` glue | Waveform look |
| **hanoi** | `GET`/`INPUT` play, `VDU 17` disc colours | Wrap + disc 7≠8 (`128+DISC-(DISC>7)`) | Play + disc 8 red OK (2026-08-15) |
| **animal** | Interactive tree, `OPENIN`/`OPENOUT` `animal.dat`, `FNquery` loop | Short STRIP/ART/QUERY/INPUT snippets | Play + save the tree |
| **fern** | Long `DRAW` chaos; `UNTIL FALSE` | Parked `graphics_confirm` only | Draws OK (2026-08-15) |

Russell `clock.bbc` (`DIM … EXT#`, `OSCLI LOAD` / `MDISPLAY` of `clock.bmp`) is **not** a regular example — same class as SYS / OpenGL demos. Use `basics/Clock.bas` or `jclock`. See [OSCLI and SYS](LANGUAGE_FEATURES_1.00.md#oscli-and-sys).

## Rule

- **Keep** a test when it asserts a fragment the program would crash or mis-parse without (kernel, glue, XOR, file stub).
- **Do not** treat that as “the program is tested.”
- **User confirmation only** for the row’s last column: look, play, timing, mouse.

Already confirmed (2026): welcome, squares, saucer, flier, soccerball, wheel, jclock, filters, hanoi, animal.

Not a substitute for that list: phase1 pytest (including animal snippets).
