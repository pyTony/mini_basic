     5 CLS
    10 W = 80
    20 H = 25
    25 M = 16
    30 DIM palette(255)
    40 FOR c = 0 TO M - 1
    50   palette(c) = (c MOD 7) + 1
    60 NEXT c
    70 FOR Y = 0 TO H - 1
    80   FOR X = 0 TO W - 1
    90     cr = (X - 50) / 20.0
   100     ci = (Y - 12) / 10.0
   110     zr = 0: zi = 0: i = 0
   120     FOR i = 0 TO M - 1
   130       temp = zr * zr - zi * zi + cr
   140       zi = 2 * zr * zi + ci
   150       zr = temp
   160       IF (zr * zr + zi * zi >= 4) THEN EXIT FOR
   170     NEXT i
   180     IF i >= M THEN
   190       COLOUR 0
   200       PRINT " ";
   210     ELSE
   220       COLOUR palette(i)
   230       PRINT "#";
   240     ENDIF
   250   NEXT X
   260   PRINT ""
   270 NEXT Y
   280 COLOUR 7
   285 PRINT BG$(7)
   290 PRINT "Finished"
   300 END
