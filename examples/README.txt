mini-BASIC example programs
============================

Project root: parent of this examples/ folder.
Tests: ../test/   Main README: ../README.md

Run from project root (mini_basic):

  python mini_basic.py --dialect mits examples/mits/menu.bas
  python mini_basic.py --dialect bbc  examples/bbc/menu.bas
  python mini_basic.py examples/mini/hello_args.bas hello world
  python mini_basic.py --quiet examples/mini/colors.bas

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

Graphics demos (pygame window; --pygame also keeps the window open after END):
  python mini_basic.py --pygame examples/mini/bbc_graphics_demo.bas
  python mini_basic.py --pygame examples/mini/sprites_demo.bas

Museum anchors (now in examples/museum/)
--------------------------------------------

  ELIZA.BAS   mits anchor — numbered GOTO, unchanged Weizenbaum logic
  BETH.BAS    bbc anchor  — structured rewrite of ELIZA

  python mini_basic.py --dialect mits examples/museum/ELIZA.BAS
  python mini_basic.py --dialect bbc  examples/museum/BETH.BAS
  python experiments/eliza_beth.py eliza

REPL quick reference: H.=HELP  L.=LIST  LO.=LOAD  MA.=MATRIX