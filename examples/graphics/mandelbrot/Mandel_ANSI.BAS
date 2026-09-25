    10     PRINT "Mandelbrot - ANSI color"
    20     PRINT "Start"
    30     TIME = 0
    40     Z$ = ".,'~=+:;*%&$OXB#@ "
    50     F = 50
    60     FOR Y = -12 TO 12
    70         FOR X = -49 TO 29
    80             C = X * 229 / 100
    90             D = Y * 416 / 100
   100             A = C
   110             B = D
   120             I = 0
   130             WHILE I < 16
   140                 Q = B / F
   150                 S = B - (Q * F)
   160                 T = ((A * A) - (B * B)) / F + C
   170                 B = 2 * ((A * Q) + (A * S / F)) + D
   180                 A = T
   190                 P = A / F
   200                 Q = B / F
   210                 IF (P * P) + (Q * Q) >= 5 THEN
   220                 PRINT FG$(I MOD 8); MID$(Z$, I + 1, 1);
   230                     BREAK
   240                 ENDIF
   250                 I = I + 1
   260             WEND
   270             IF I >= 16 THEN PRINT" ";
   280         NEXT X
   290         PRINT RESET$()
   300     NEXT Y
   310     Q = TIME
   320 PRINT "Finished"
   330 PRINT FG$(2);"Time: "; Q / 100;" secs."; RESET$()
   340 END
