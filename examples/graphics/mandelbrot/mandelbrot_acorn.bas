      REM Mandelbrot without EXIT — Acorn BBC BASIC V compatible idiom
      REM (RISC OS BBC BASIC V has no EXIT FOR/WHILE/REPEAT)
      PRINT "Start"
      TIME = 0
      Z$ = ".,'~=+:;*%&$OXB#@ "
      F = 50
      FOR Y = -12 TO 12
        FOR X = -49 TO 29
          C = X * 229 / 100
          D = Y * 416 / 100
          A = C : B = D : I = 0
          done% = FALSE
          REPEAT
            Q = B / F : S = B - (Q * F)
            T = ((A * A) - (B * B)) / F + C
            B = 2 * ((A * Q) + (A * S / F)) + D
            A = T : P = A / F : Q = B / F
            IF (P * P) + (Q * Q) >= 5 THEN
              PRINT MID$(Z$, I + 1, 1);
              done% = TRUE
            ELSE
              I = I + 1
            ENDIF
          UNTIL I >= 16 OR done%
          IF I >= 16 AND NOT done% THEN PRINT " ";
        NEXT X
        PRINT
      NEXT Y
      PRINT "Finished"
      PRINT "Time: "; TIME / 100; " secs."
      END