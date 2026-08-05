    10 W = 80
    20 H = 25
    30 DIM palette(255)
    40 FOR c = 0 TO 254
    50   palette(c) = (c MOD 7) + 1
    60 NEXT c
    70 FOR Y = 0 TO H - 1
    80   FOR X = 0 TO W - 1
    90     i = (X + Y) MOD 7 + 1
   100     COLOUR palette(i)
   110     PRINT "#";
   120   NEXT X
   130   PRINT ""
   140 NEXT Y
   150 COLOUR 7
   160 PRINT "Done"
   170 END
   180 NEXT Y
   190 COLOUR 7
   200 PRINT "Done"
   210 END
