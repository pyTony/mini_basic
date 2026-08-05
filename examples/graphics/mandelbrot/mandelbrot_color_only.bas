100 PRINT "Mandelbrot - ANSI color only"
110 PRINT "Start"
120 TIME = 0
125 ITER = 16
130 IF _argc >= 1 THEN ITER = ARG(1)
135 IF ITER < 1 THEN ITER = 1
140 F = 50
150 FOR Y = -12 TO 12
160   FOR X = -49 TO 29
170     C = X * 229 / 100
180     D = Y * 416 / 100
190     A = C : B = D : I = 0
200     WHILE I < ITER
210       Q = B / F : S = B - (Q * F)
220       T = ((A * A) - (B * B)) / F + C
230       B = 2 * ((A * Q) + (A * S / F)) + D
240       A = T : P = A / F : Q = B / F
250       IF (P * P) + (Q * Q) >= 5 THEN
260         H = 16 + (I * 215) / ITER
270         PRINT RESET$();BG$(H);FG$(H);" ";
280         BREAK
290       ENDIF
300       I = I + 1
310     WEND
320     IF I >= ITER THEN PRINT RESET$();BG$(232);FG$(232);" ";
330   NEXT X
340   PRINT RESET$()
350 NEXT Y
360 Q = TIME
370 PRINT "Finished"
380 PRINT FG$(2); "Time: "; Q / 100; " secs."; RESET$()
390 END