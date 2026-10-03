     5 T = TIME
    10 W = 80
    20 H = 25
    30 FOR Y = 0 TO H - 1
    40 FOR X = 0 TO W - 1
    50 cr = (X - 50) / 20.0
    60 ci = (Y - 12) / 10.0
    70     zr = 0: zi = 0: i = 0
    80     WHILE (zr * zr + zi * zi < 4) AND (i < 255)
    90       temp = zr * zr - zi * zi + cr
   100       zi = 2 * zr * zi + ci
   110       zr = temp
   120       i = i + 1
   130     WEND
   140     IF i = 255 THEN
   150       R = 0: G = 0: B = 0
   160     ELSE
   170       R = INT(127.5 * (1 + SIN(i * 0.1)))
   180       G = INT(127.5 * (1 + SIN(i * 0.15)))
   190       B = INT(127.5 * (1 + SIN(i * 0.2)))
   200     ENDIF
   205  
   210     PRINT BGRGB$(R,G,B);" ";
   220 NEXT X
   230 PRINT RESET$
   240 NEXT Y
   250 PRINT RESET$
   260 PRINT "Time:"; (TIME - T) / 100;"seconds"
   270 END
