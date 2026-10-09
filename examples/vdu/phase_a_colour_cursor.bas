REM ============================================================
REM  Phase A demo — VDU colour, cursor, bell, resets
REM  Codes: 7, 8-11, 12, 13, 17, 20, 26, 30, 31
REM ============================================================
REM  Run:
REM    python -m mini_basic --dialect bbc examples/vdu/phase_a_colour_cursor.bas
REM
REM  Each step: CLS + full caption, then a short demo line.
REM ============================================================

MODE 3
VDU 20
VDU 26
CLS
PRINT "=== Phase A: VDU colour & cursor ==="
PRINT
PRINT "Captions stay full-screen; demos are short."
WAIT 140

REM --- 1 colour fg ---
CLS
PRINT "Step 1 — VDU 17,n  (same as COLOUR n)"
PRINT
PRINT "  n < 128  -> text foreground"
PRINT "  n >= 128 -> text background (n-128)"
PRINT
VDU 17,1
PRINT "  This line: VDU 17,1  (foreground 1)"
WAIT 160

REM --- 2 colour bg ---
CLS
VDU 20
PRINT "Step 2 — VDU 17,129  background (128+1)"
PRINT
VDU 17,7
VDU 17,129
PRINT "  This line: fg 7 + bg 1"
WAIT 160

REM --- 3 reset colours ---
CLS
PRINT "Step 3 — VDU 20  reset text colours"
PRINT
VDU 20
PRINT "  Defaults restored (typically white on black)."
WAIT 140

REM --- 4 cursor dance on a clear lower area ---
CLS
PRINT "Step 4 — cursor moves VDU 8 9 10 11 13"
PRINT
PRINT "  Marker starts at (12,8), then L R D U and CR."
PRINT
VDU 20
VDU 31,12,8
PRINT "*";
WAIT 70
VDU 8:PRINT "L";
WAIT 50
VDU 9:VDU 9:PRINT "R";
WAIT 50
VDU 10:PRINT "D";
WAIT 50
VDU 11:PRINT "U";
WAIT 50
VDU 13
PRINT "  <-- VDU 13 carriage return (col 0)"
WAIT 160

REM --- 5 home ---
CLS
PRINT "Step 5 — VDU 30  home cursor (0,0)"
PRINT
PRINT "  Next line prints at top-left after VDU 30:"
WAIT 100
VDU 30
PRINT "[home via VDU 30]"
WAIT 140

REM --- 6 bell ---
CLS
PRINT "Step 6 — VDU 7  bell"
PRINT
PRINT "  You may hear a short beep (Ctrl+G / BEL)."
VDU 7
WAIT 120

REM --- 7 viewport reset note ---
CLS
PRINT "Step 7 — VDU 26  reset viewports"
PRINT
VDU 26
PRINT "  Viewport state cleared (see Phase B for VDU 28/24)."
PRINT
PRINT "Phase A complete."
PRINT "Next: examples/vdu/phase_b_viewports.bas"
PRINT
PRINT "Ctrl+C or Escape to close."
WAIT 250
END
