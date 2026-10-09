REM ============================================================
REM  Phase C demo — VDU 23 multi-byte commands
REM  Codes: 23,1 · 23,22 · 23,0 / 23,16 stubs
REM ============================================================
REM  Run:
REM    python -m mini_basic --dialect bbc examples/vdu/phase_c_vdu23.bas
REM
REM  Each step on a clear full screen for readability.
REM ============================================================

MODE 3
VDU 20
VDU 26
CLS
PRINT "=== Phase C: VDU 23 known + stubs ==="
PRINT
PRINT "VDU 23 is multi-byte. Known codes do real work;"
PRINT "unknown codes are accepted without crashing."
WAIT 160

CLS
PRINT "Step 1 — VDU 23,1,0  hide caret (like OFF)"
PRINT
VDU 23,1,0
PRINT "  Caret hidden."
WAIT 140

CLS
PRINT "Step 2 — VDU 23,1,1  show caret (like ON)"
PRINT
VDU 23,1,1
PRINT "  Caret shown again."
WAIT 140

CLS
PRINT "Step 3 — VDU 23,0,...  STUB (no crash)"
PRINT
PRINT "  BBCSDL/RISC OS often sends caret geometry here."
PRINT "  mini_basic consumes the bytes and continues."
VDU 23,0,10,0,0;0;0;
PRINT
PRINT "  OK: VDU 23,0,10,0,0;0;0; finished."
WAIT 160

CLS
PRINT "Step 4 — VDU 23,16,...  STUB (no crash)"
PRINT
VDU 23,16,64,0,0,0,0,0,0,0
PRINT "  OK: VDU 23,16,64,0,0,0,0,0,0,0 finished."
WAIT 140

CLS
PRINT "Step 5 — VDU 23,22 custom size (BBCSDL)"
PRINT
PRINT "  VDU 23,22,320;256;8,16,16,128"
PRINT "  May resize the graphics canvas if pygame is on."
WAIT 120
VDU 23,22,320;256;8,16,16,128
CLS
PRINT "After VDU 23,22 — mode/canvas may have changed."
PRINT
PRINT "Phase C complete."
PRINT
PRINT "All demos:"
PRINT "  examples/vdu/phase_a_colour_cursor.bas"
PRINT "  examples/vdu/phase_b_viewports.bas"
PRINT "  examples/vdu/phase_c_vdu23.bas"
PRINT
PRINT "Ctrl+C or Escape to close."
WAIT 280
END
