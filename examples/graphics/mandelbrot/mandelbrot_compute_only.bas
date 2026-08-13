10 REM Compute-only Mandelbrot — isolates WHILE/CONT AND compute cost from drawing.
20 REM Same math/loop shape as mandelbrot_archimedes_mode9.bas; no MODE/GCOL/RECTANGLE/*REFRESH.
30 REM python -m mini_basic --dialect bbc examples/graphics/mandelbrot/mandelbrot_compute_only.bas
40 XMIN = -2.25: XMAX = 0.75
50 YMIN = -1.35: YMAX = 1.35
60 MAXITER% = 24
70 NX% = 640: NY% = 512
80 ST% = 4
90 DIM RESULT%(NY% / ST%, NX% / ST%)
100 TIME = 0
110 RY% = 0
120 FOR PY% = 0 TO NY% - ST% STEP ST%
130   CY = YMIN + (PY% / (NY% - 1)) * (YMAX - YMIN)
140   RX% = 0
150   FOR PX% = 0 TO NX% - ST% STEP ST%
160     CX = XMIN + (PX% / (NX% - 1)) * (XMAX - XMIN)
170     I% = 0: ZX = 0: ZY = 0: CONT = -1
180     WHILE CONT AND (I% < MAXITER%)
190       TEMP = ZX * ZX - ZY * ZY
200       ZY = 2 * ZX * ZY + CY
210       ZX = TEMP + CX
220       I% = I% + 1
230       CONT = (ZX * ZX + ZY * ZY < 4)
240     ENDWHILE
250     RESULT%(RY%, RX%) = I%
260     RX% = RX% + 1
270   NEXT PX%
280   RY% = RY% + 1
290 NEXT PY%
300 T = TIME
310 PRINT "Done "; T / 100; "s (compute only, no drawing)"
320 PRINT "Sample RESULT%(0,0)="; RESULT%(0,0); " RESULT%(10,10)="; RESULT%(10,10)
330 END
