' dialect: mini
REM Unnumbered pretty listing of examples/graphics/mandelbrot/mandelbrot_color_only.bas
PRINT "Mandelbrot - ANSI color only"
PRINT "Start"
TIME = 0
ITER = 16
IF _argc >= 1 THEN ITER = ARG(1)
IF ITER < 1 THEN ITER = 1
F = 50
FOR Y = -12 TO 12
    FOR X = -49 TO 29
        C = X * 229 / 100
        D = Y * 416 / 100
        A = C: B = D: I = 0
        WHILE I < ITER
            Q = B / F: S = B - (Q * F)
            T = ((A * A) - (B * B)) / F + C
            B = 2 * ((A * Q) + (A * S / F)) + D
            A = T: P = A / F: Q = B / F
            IF (P * P) + (Q * Q) >= 5 THEN
                H = 16 + (I * 215) / ITER
                PRINT RESET$();BG$(H);FG$(H);" ";
                BREAK
            ENDIF
            I = I + 1
        ENDWHILE
        IF I >= ITER THEN PRINT RESET$();BG$(232);FG$(232);" ";
    NEXT X
    PRINT RESET$()
NEXT Y
Q = TIME
PRINT "Finished"
PRINT FG$(2);"Time: "; Q / 100;" secs."; RESET$()
END
