' dialect: mini
' Mandelbrot + ANSI colours (FG$/RESET$). Works with WEND or ENDWHILE.
' BBCSDL portability: ENDWHILE / EXIT WHILE (SDL rejects WEND / BREAK).
10 PRINT "Mandelbrot - ANSI color"
20 PRINT "Start"
30 TIME = 0
40 ITER = 16
50 Z$ = ".,'~=+:;*%&$OXB#@ "
60 F = 50
70 FOR Y = -12 TO 12
80   FOR X = -49 TO 29
90     C = X * 229 / 100
100    D = Y * 416 / 100
110    A = C
120    B = D
130    I = 0
140    WHILE I < ITER
150      Q = B / F
160      S = B - (Q * F)
170      T = ((A * A) - (B * B)) / F + C
180      B = 2 * ((A * Q) + (A * S / F)) + D
190      A = T
200      P = A / F
210      Q = B / F
220      IF (P * P) + (Q * Q) >= 5 THEN
230        REM FG$(0)=black looks blank on black terminals — use 1..7 only
240        PRINT FG$((I MOD 7) + 1); MID$(Z$, I + 1, 1);
250        EXIT WHILE
260      ENDIF
270      I = I + 1
280    ENDWHILE
290    IF I >= ITER THEN PRINT " ";
300  NEXT X
310  PRINT RESET$()
320 NEXT Y
330 Q = TIME
340 PRINT "Finished"
350 PRINT FG$(2); "Time: "; Q / 100; " secs."; RESET$()
360 END
