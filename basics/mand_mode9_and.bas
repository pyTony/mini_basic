1 REM dialect: bbc
    10 REM Full-screen Mandelbrot MODE 9 (640x512, OS scale 2) — SDL-like solid blocks.
    20 REM Do not use lone PLOT 69 with STEP: THAT LEAVES BLACK GAPS BETWEEN SAMPLES.
    30 REM RECTANGLE FILL size matches STEP so tiles abut (see BBCSDL reference look).
    40 REM python -m mini_basic --pygame --dialect bbc basics/mand_mode9_and.bas
    50 MODE 9
    60 VDU 20
    70 COLOUR 7: COLOUR 128
    80 OFF
    90 CLG
   100 PRINT TAB(0,0);"Mandelbrot M9"
   110 TIME = 0
   120 XMIN = -2.25: XMAX = 0.75
   130 YMIN = -1.35: YMAX = 1.35
   140 MAXITER% = 24
   150 NX% = 640: NY% = 512
   160 ST% = 4
   170 REM OS units: SCALE 2 = > ST% SCREEN PIXELS NEED BW% = ST%* 2
   180 BW% = ST% * 2: BH% = ST% * 2
   190 *REFRESH OFF
   200 FOR PY% = 0 TO NY% - ST% STEP ST%
   210   CY = YMIN + (PY% / (NY% - 1)) * (YMAX - YMIN)
   220   FOR PX% = 0 TO NX% - ST% STEP ST%
   230     CX = XMIN + (PX% / (NX% - 1)) * (XMAX - XMIN)
   240     I% = 0: ZX = 0: ZY = 0
   250     WHILE (I% < MAXITER%) AND (ZX * ZX + ZY * ZY < 4)
   260       TEMP = ZX * ZX - ZY * ZY
   270       ZY = 2 * ZX * ZY + CY
   280       ZX = TEMP + CX
   290       I% = I% + 1
   310     ENDWHILE
   320     IF I% < MAXITER% THEN
   330       COL% = (I% MOD 7) + 1
   340       GCOL 0, COL%
   350       RECTANGLE FILL PX% * 2, PY% * 2, BW%, BH%
   360     ENDIF
   370   NEXT PX%
   380   *REFRESH
   390 NEXT PY%
   400 *REFRESH ON
   410 T = TIME
   420 PRINT TAB(0,31);"Done "; T / 100;"s"
   430 END
