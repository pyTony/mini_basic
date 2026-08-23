100 PRINT "Mandelbrot - ANSI color"
110 PRINT "Start"
120 TIME = 0
130 Z$ = ".,'~=+:;*%&$OXB#@ "
140 F = 50
150 FOR Y = -12 TO 12
160     FOR X = -49 TO 29
170         C = X * 229 / 100
180         D = Y * 416 / 100
190         A = C: B = D: I = 0
200         WHILE I < 16
210             Q = B / F: S = B - (Q * F)
220             T = ((A * A) - (B * B)) / F + C
230             B = 2 * ((A * Q) + (A * S / F)) + D
240             A = T: P = A / F: Q = B / F
250             IF (P * P) + (Q * Q) >= 5 THEN
260                 PRINT FG$(I MOD 8); MID$(Z$, I + 1, 1);
270                 EXIT FOR
280             ENDIF
290             I = I + 1
300         ENDWHILE
310         IF I >= 16 THEN PRINT" ";
320     NEXT X
330     PRINT RESET$()
340 NEXT Y
350 Q = TIME
360 PRINT "Finished"
370 PRINT FG$(2);"Time: "; Q / 100;" secs."; RESET$()
380 END
