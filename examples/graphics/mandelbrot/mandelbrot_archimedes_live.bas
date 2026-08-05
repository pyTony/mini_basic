    10 REM Mandelbrot for Archimedes Live (RISC OS BBC BASIC V)
    20 REM Paste this file exactly — do not use *REFRESH or *FX 112/113
    30 MODE 2
    40 OFF
    50 PRINT TAB(0,0);"Mandelbrot MODE 2"
    60 TIME = 0
    70 FOR Y = -12 TO 12
    80   FOR X = -49 TO 29
    90     CX = X * 229 / 100
   100     CY = Y * 416 / 100
   110     ZX = CX : ZY = CY : I% = 0
   120     REPEAT
   130       TEMP = ZX * ZX - ZY * ZY
   140       ZY = 2 * ZX * ZY + CY
   150       ZX = TEMP / 50 + CX
   160       I% = I% + 1
   170     UNTIL I% >= 16 OR ZX * ZX + ZY * ZY >= 5
   180     IF I% < 16 THEN COL% = (I% MOD 7) + 1 : GCOL 0, COL% : PLOT 69, (X + 49) * 16, (Y + 12) * 40
   190   NEXT X
   200 NEXT Y
   210 T = TIME
   220 PRINT TAB(0,24);"Finished in ";T/100;" s"
   230 END