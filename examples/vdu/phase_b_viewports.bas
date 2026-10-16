REM ============================================================
REM  Phase B demo — text and graphics viewports (clean layout)
REM  Codes: 24, 26, 28, 30, 31
REM ============================================================
REM  Run:
REM    python -m mini_basic --dialect bbc examples/vdu/phase_b_viewports.bas
REM
REM  Layout rule for this demo:
REM    - Explanations always on FULL screen (after VDU 26 + CLS).
REM    - Inside a text window we only print short markers, then restore.
REM    That avoids overwriting mess when VDU 30 homes to the window.
REM ============================================================

MODE 8
OFF
ORIGIN 0,0
VDU 26
CLS
PRINT "=== Phase B: VDU viewports ==="
PRINT
PRINT "This demo uses full-screen captions, then a short"
PRINT "window demo, then restores with VDU 26 so text stays readable."
PRINT
PRINT "Waiting..."
WAIT 180

REM ---------- Step 1: explain VDU 28, then show window ----------
VDU 26
CLS
PRINT "Step 1 — VDU 28 text window"
PRINT
PRINT "  VDU 28,left,bottom,right,top"
PRINT "  Example: VDU 28,8,18,55,6"
PRINT
PRINT "  Character cells: cols 8..55, rows 6..18"
PRINT "  Cursor jumps to top-left of that window."
PRINT
PRINT "  Next: short messages ONLY inside the window."
WAIT 200

VDU 28,8,18,55,6
PRINT ">>> INSIDE text window (VDU 28)"
PRINT ">>> row 2 of window"
PRINT ">>> row 3 of window"
WAIT 200

REM ---------- Step 2: clamp VDU 31 ----------
VDU 26
CLS
PRINT "Step 2 — VDU 31 clamps into the window"
PRINT
PRINT "  After VDU 28,5,18,50,8 :"
PRINT "  VDU 31,0,0 does NOT go to screen (0,0)."
PRINT "  It clamps to the window top-left."
WAIT 180

VDU 28,5,18,50,8
VDU 31,0,0
PRINT "[VDU 31,0,0 -> clamped to window top-left]"
WAIT 180

REM ---------- Step 3: VDU 30 homes to window ----------
VDU 26
CLS
PRINT "Step 3 — VDU 30 homes to WINDOW top-left"
PRINT
PRINT "  Mid-window marker, then VDU 30, then home tag."
WAIT 160

VDU 28,6,18,52,7
VDU 31,20,12
PRINT "(mid)"
WAIT 100
VDU 30
PRINT "[VDU 30 = window home]"
WAIT 180

REM ---------- Step 4: graphics viewport + diagonal ----------
VDU 26
CLS
PRINT "Step 4 — VDU 24 graphics window (OS units)"
PRINT
PRINT "  VDU 24,x1;y1;x2;y2;   (semicolon = 16-bit words)"
PRINT "  Example: VDU 24,40;40;500;350;"
PRINT
PRINT "  Stores the region; sample red diagonal drawn."
PRINT "  (Pixel clip may still be soft in 1.00.)"
WAIT 180

VDU 24,40;40;500;350;
GCOL 0,1
MOVE 40,40
DRAW 500,350
WAIT 200

REM ---------- Step 5: VDU 26 reset ----------
VDU 26
CLS
PRINT "Step 5 — VDU 26 reset BOTH viewports"
PRINT
PRINT "  Text window and graphics window cleared."
PRINT "  This caption is full-screen again."
PRINT
PRINT "Phase B complete."
PRINT "Next: examples/vdu/phase_c_vdu23.bas"
PRINT
PRINT "Ctrl+C or Escape to close."
WAIT 300
END
