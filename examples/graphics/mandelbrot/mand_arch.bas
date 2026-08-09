1 REM dialect: bbc
10 REM Coarse Mandelbrot — MODE 2, Archimedes OS units (scale 8x4).
20 REM True float iteration (not the old broken TEMP/50 hybrid).
30 REM Fat RECTANGLE blocks so the set is visible; progressive refresh.
40 REM Run: python -m mini_basic --dialect bbc examples/graphics/mandelbrot/mand_arch.bas
50 MODE 2
60 OFF
70 CLG
80 COLOUR 7
90 PRINT TAB(0,0);"Mandelbrot M2"
100 TIME = 0
110 XMIN = -2.2 : XMAX = 0.75
120 YMIN = -1.25 : YMAX = 1.25
130 MAXITER% = 20
140 REM MODE 2 pixels 160x256; plot in OS units (0..1279, 0..1023)
150 W% = 160 : H% = 256
160 ST% = 4
170 SW% = ST% * 8 : SH% = ST% * 4
180 *REFRESH OFF
190 FOR PY% = 0 TO H% - ST% STEP ST%
200   CY = YMIN + (PY% / (H% - 1)) * (YMAX - YMIN)
210   FOR PX% = 0 TO W% - ST% STEP ST%
220     CX = XMIN + (PX% / (W% - 1)) * (XMAX - XMIN)
230     I% = 0 : ZX = 0 : ZY = 0 : CONT = -1
240     WHILE CONT AND (I% < MAXITER%)
250       TEMP = ZX * ZX - ZY * ZY
260       ZY = 2 * ZX * ZY + CY
270       ZX = TEMP + CX
280       I% = I% + 1
290       CONT = (ZX * ZX + ZY * ZY < 4)
300     ENDWHILE
310     IF I% < MAXITER% THEN
320       COL% = (I% MOD 7) + 1
330       GCOL 0, COL%
340       OX% = PX% * 8
350       OY% = PY% * 4
360       RECTANGLE FILL OX%, OY%, SW%, SH%
370     ENDIF
380   NEXT PX%
390   REM show each band so the screen is not black until the end
400   *REFRESH
410 NEXT PY%
420 *REFRESH ON
430 T = TIME
440 PRINT TAB(0,30);"Done "; T / 100; "s"
450 END
