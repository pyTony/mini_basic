    REM CHARACTER MANDELBROT
    W = 78
    H = 22
    MI = 48
    FOR PY = 0 TO H - 1
        CI = -1.15 + PY / H * 2.3
        FOR PX = 0 TO W - 1
            CR = -2.35 + PX / W * 1.15
            ZR = 0
            ZI = 0
            CNT = 0
            FOR K = 1 TO MI
                ZR2 = ZR * ZR - ZI * ZI + CR
                ZI2 = 2 * ZR * ZI + CI
                MAG2 = ZR2 * ZR2 + ZI2 * ZI2
                IF MAG2 > 4 THEN
                    BREAK
                ENDIF
                ZR = ZR2
                ZI = ZI2
                CNT = K
            NEXT K
            REM % is not modulo in mini_basic (reserved for A% / %1010); use MOD
            CH = ASC(" ") + (CNT MOD 11) * 6
            PRINT CHR$(CH);
        NEXT PX
        PRINT
    NEXT PY
    END
