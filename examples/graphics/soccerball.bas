    10 REM Spinning soccer ball (speed - adjusted for Python interpreter)
    20 REM Keep p, q, r, s, t
    30 MODE 9: OFF
    40 ORIGIN 640,512: COLOR 130
    50 DIM XYZ(2,59), TMP(2,59), B(2,2), C(2,2)
    60 S = SQR5 + 1: P = S / 2: Q = P + 2: R = S + 1: T = P * 3
    70 FOR I% = 0 TO 59
    80 READ XYZ(0,I%), XYZ(1,I%), XYZ(2,I%)
    90 NEXT
   100 * REFRESH OFF
   110 B = 0.5: C = 0
   120 B() = COS(B), 0, -SIN(B), 0, 1, 0, SIN(B), 0, COS(B)
   130 REPEAT
   140 C() = COS(C), SIN(C), 0, -SIN(C), COS(C), 0, 0, 0, 1
   150 C() = B() . C(): TMP() = C() . XYZ()
   160 CLS
   170 GCOL 3: CIRCLE FILL 0, 0, 432: GCOL 0
   180 I% = 0
   190 FOR J% = 0 TO 11
   200 Z = SUM(TMP(1, I%TO I% + 4))
   210 FOR K% = 0 TO 4
   220 X% = 3200 * TMP(0,I%) / (36 + TMP(1,I%))
   230 Y% = 3200 * TMP(2,I%) / (36 + TMP(1,I%))
   240 IF K%<2 MOVE X%,Y%ELSE IF Z<-2.5 PLOT 85,X%,Y%
   250 I% += 1
   260 NEXT
   270 NEXT J%
   280 WAIT 1
   290 * REFRESH
   300 C += 0.03
   310 UNTIL FALSE
   320 END
   330 DATA 0, 1, T, -P, 2, R, P, 2, R, -1, Q, S, 1, Q, S
   340 DATA 0, 1, -T, -P, 2, -R, P, 2, -R, -1, Q, -S, 1, Q, -S
   350 DATA 0, -1, T, -P, -2, R, P, -2, R, -1, -Q, S, 1, -Q, S
   360 DATA 0, -1, -T, -P, -2, -R, P, -2, -R, -1, -Q, -S, 1, -Q, -S
   370 DATA 1, T, 0, 2, R, -P, 2, R, P, Q, S, -1, Q, S, 1
   380 DATA 1, -T, 0, 2, -R, -P, 2, -R, P, Q, -S, -1, Q, -S, 1
   390 DATA -1, T, 0, -2, R, -P, -2, R, P, -Q, S, -1, -Q, S, 1
   400 DATA -1, -T, 0, -2, -R, -P, -2, -R, P, -Q, -S, -1, -Q, -S, 1
   410 DATA T, 0, 1, R, -P, 2, R, P, 2, S, -1, Q, S, 1, Q
   420 DATA T, 0, -1, R, -P, -2, R, P, -2, S, -1, -Q, S, 1, -Q
   430 DATA -T, 0, 1, -R, -P, 2, -R, P, 2, -S, -1, Q, -S, 1, Q
   440 DATA -T, 0, -1, -R, -P, -2, -R, P, -2, -S, -1, -Q, -S, 1, -Q
   450 DATA -T, 0, -1, -R, -P, -2, -R, P, -2, -S, -1, -Q, -S, 1, -Q
