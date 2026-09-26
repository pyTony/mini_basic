PRINT "Mandelbrot - ANSI color"
PRINT "Start"
TIME = 0
Z$ = ".,'~=+:;*%&$OXB#@ "
F = 50
FOR Y = -12 TO 12
    FOR X = -49 TO 29
        C = X * 229 / 100
        D = Y * 416 / 100
        A = C
        B = D
        I = 0
        WHILE I < 16
            Q = B / F
            S = B - (Q * F)
            T = ((A * A) - (B * B)) / F + C
            B = 2 * ((A * Q) + (A * S / F)) + D
            A = T
            P = A / F
            Q = B / F
            IF (P * P) + (Q * Q) >= 5 THEN
                PRINT FG$(I MOD 8); MID$(Z$, I + 1, 1);
                BREAK
            ENDIF
            I = I + 1
        ENDWHILE
        IF I >= 16 THEN PRINT" ";
    NEXT X
    PRINT RESET$()
NEXT Y
Q = TIME
PRINT "Finished"
PRINT FG$(2);"Time: "; Q / 100;" secs."; RESET$()
END
