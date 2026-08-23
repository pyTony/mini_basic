10 REM Mandelbrot - BBC BASIC Graphics
20 REM Adapted for Archimedes BBC Micro color graphics
30 MODE 2
40 TIME = 0
50 Z$ = " .,'`~=+:;*%&$0XB#@ "
60 F = 50
70 FOR Y = -12 TO 12
80     FOR X = -49 TO 29
90         C = X * 229 / 100
100         D = Y * 416 / 100
110         A = C: B = D: I = 0
120         WHILE I < 16
130             Q = B / F: S = B - (Q * F)
140             T = ((A * A) - (B * B)) / F + C
150             B = 2 * ((A * Q) + (A * S / F)) + D
160             A = T: P = A / F: Q = B / F
170             IF (P * P) + (Q * Q) >= 5 THEN
180                 base_color% = (I DIV 4) MOD 64
190                 tint_level% = (I MOD 4) * 64
200                 COLOUR base_color%
210                 TINT 0, tint_level%
220                 PRINT MID$(Z$, I + 1, 1);
230                 I = 999
240             ENDIF
250             I = I + 1
260         ENDWHILE
270         IF I = 16 THEN PRINT" ";
280     NEXT X
290     PRINT ""
300 NEXT Y
310 Q = TIME
320 PRINT "Finished"
330 PRINT "Time: "; Q / 100;" secs."
340 END
