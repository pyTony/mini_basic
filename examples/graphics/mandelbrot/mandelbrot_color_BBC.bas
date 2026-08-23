100 REM Mandelbrot colour — same layout as mandelbrot2.bas (SDL 2.0)
110 PRINT "Mandelbrot - BBC colour"
120 PRINT "Start"
130 TIME = 0
140 Z$ = ".,'~=+:;*%&$OXB#@ "
150 F = 50
160 FOR Y = -12 TO 12
170     FOR X = -49 TO 29
180         C = X * 229 / 100
190         D = Y * 416 / 100
200         A = C: B = D: I = 0
210         WHILE I < 16
220             Q = B / F: S = B - (Q * F)
230             T = ((A * A) - (B * B)) / F + C
240             B = 2 * ((A * Q) + (A * S / F)) + D
250             A = T: P = A / F: Q = B / F
260             IF (P * P) + (Q * Q) >= 5 THEN
270                 COLOUR I + 1
280                 PRINT MID$(Z$, I + 1, 1);
290                 EXIT WHILE
300             ENDIF
310             I = I + 1
320         ENDWHILE
330         IF I >= 16 THEN PRINT" ";
340     NEXT X
350     PRINT ""
360 NEXT Y
370 Q = TIME
380 COLOUR 7
381 REM reset TO white / default
390 PRINT "Finished"
400 PRINT "Time: "; Q / 100;" secs."
410 END
