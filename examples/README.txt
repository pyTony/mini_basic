mini-BASIC example programs
============================

Project root: parent of this examples/ folder.
Tests: ../test/   Main README: ../README.md

Git (this tree):
  https://github.com/pyTony/mini_basic
  https://github.com/pyTony/mini_basic/tree/main/examples

Upstream (third-party sources):
  M6502 C-port:  https://github.com/garyexplains/BASIC-M6502-CPORT
  BBCSDL demos:  https://github.com/rtrussell/BBCSDL/tree/master/examples
                 https://www.bbcbasic.co.uk/bbcsdl/examples/index.html

Handbook: ../index.html  (pages in ../docs/site/)
Install interpreter: pip install "mini-basic @ git+https://github.com/pyTony/mini_basic.git"
Examples themselves are in this git tree (not the pip wheel).

Run from the clone root:

  python -m mini_basic --dialect mits examples/mits/menu.bas
  python -m mini_basic --dialect bbc  examples/bbc/menu.bas
  python -m mini_basic examples/mini/hello_args.bas hello world
  python -m mini_basic -q examples/mini/colors.bas
  python -m mini_basic --dialect mits examples/m6502-cport/01_hello.bas

Dialect folders
---------------

examples/mits/   Numbered lines, GOTO, ON GOTO, ON ERROR, ? = PRINT
  menu.bas       ON GOTO dispatch menu (try choices 1, 2, 3)
  on_error.bas   ON ERROR GOTO + RESUME NEXT after READ error
  question.bas   ? shorthand for PRINT

examples/bbc/    Unnumbered structured style (BETH.BAS cousin)
  menu.bas       WHILE / IF / ELSEIF — same logic as mits/menu.bas
  goto_label.bas GOTO to a label (BBC has GOTO; BETH avoids it by choice)
  repeat.bas     REPEAT/UNTIL and EXIT REPEAT
  proc.bas       DEF PROC / PROC / ENDPROC
  time.bas       TIME centisecond clock with REPEAT/UNTIL

examples/mini/   Full superset (default dialect)
  hello_args.bas CLI args: _argc, ARG(n), ARG$(n)
  colors.bas     FG$/BG$ ANSI color demo
  break_continue.bas BREAK/CONTINUE with loop labels (mini only)
  bbc_graphics_demo.bas  BBC MODE/PLOT/DRAW shapes (needs --pygame)
  sprites_demo.bas       SPRITEDEF/SPRITE demo (needs --pygame)

examples/m6502-cport/  Microsoft BASIC M6502 C-port tutorials (01–48 automated)

Graphics demos (optional pygame extra; --pygame keeps the window open after END):
  python -m mini_basic --pygame examples/mini/bbc_graphics_demo.bas
  python -m mini_basic --pygame examples/mini/sprites_demo.bas
  python -m mini_basic --pygame --dialect bbc examples/graphics/jclock.bas
  python -m mini_basic --pygame examples/graphics/soccerball.bas

  examples/graphics/ holds native PLOT/CIRCLE/VDU ports (and a few .bbc
  that LIST as ordinary BBC). BBCSDL library / texture / MDISPLAY demos
  stay upstream. Inspect a tokenized file with:
    python -m mini_basic --list --dialect bbc --display none file.bbc

Museum anchors (examples/museum/; copies in basics/ for archive installs)
--------------------------------------------

  ELIZA.BAS   mits — Weizenbaum/Shrager/North numbered DOCTOR
  BETH.BAS    bbc  — same therapy DATA, structured WHILE/IF (produced from ELIZA)

  python -m mini_basic --dialect mits examples/museum/ELIZA.BAS
  python -m mini_basic --dialect bbc  examples/museum/BETH.BAS
  python -m mini_basic --dialect mits basics/ELIZA.BAS
  python -m mini_basic --dialect bbc  basics/BETH.BAS

REPL quick reference: H.=HELP  L.=LIST  LO.=LOAD  MA.=MATRIX