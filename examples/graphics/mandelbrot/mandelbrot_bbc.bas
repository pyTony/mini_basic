100 REM Mandelbrot with proper exit
105 REM WAIT -1 ignores window close in BBC SDL; ON CLOSE QUIT fixes that.
106 ON CLOSE QUIT
107 REM Use Run (F9), not debug-step: the old EXIT WHILE fired 1000+ times.
108 REM MODE 3
109 CLS
110 COLOUR 7,0
111 PRINT "Start"
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
260                 COLOUR I + 1, 0
270                 PRINT MID$(Z$, I + 1, 1);
280                 I = 999
290             ENDIF
300             I = I + 1
310         ENDWHILE
320         IF I >= 16 AND I < 999 THEN PRINT" ";
350     NEXT X
360     PRINT
370 NEXT Y
375 *REFRESH
380 Q = TIME
390 COLOUR 7,0
400 PRINT "Finished"
410 PRINT "Time: "; Q / 100;" secs."
420 COLOUR 6,0
430 PRINT "Close window to exit"
440 REM Mandelbrot is done. Run (F9) — do not step: WAIT stops the debugger once.
450 WAIT -1
460 END
