REM Spinning soccer ball (speed-adjusted for Python interpreter)
REM Keep p, q, r, s, t
MODE 9: OFF
ORIGIN 640,512: COLOUR 130
DIM XYZ(2,59), TMP(2,59), B(2,2), C(2,2)
S = SQR5 + 1: P = S / 2: Q = P + 2: R = S + 1: T = P * 3
FOR I%= 0 TO 59
READ XYZ(0,I%), XYZ(1,I%), XYZ(2,I%)
NEXT
*REFRESH OFF
B = 0.5: C = 0
B() = COS(B), 0, -SIN(B), 0, 1, 0, SIN(B), 0, COS(B)
REPEAT
C() = COS(C), SIN(C), 0, -SIN(C), COS(C), 0, 0, 0, 1
C() = B() . C(): TMP() = C() . XYZ()
CLS
GCOL 3: CIRCLE FILL 0, 0, 432: GCOL 0
I%= 0
FOR J%= 0 TO 11
Z = SUM(TMP(1, I% TO I% + 4))
FOR K%= 0 TO 4
X%= 3200 * TMP(0,I%) / (36 + TMP(1,I%))
Y%= 3200 * TMP(2,I%) / (36 + TMP(1,I%))
IF K%<2 MOVE X%,Y% ELSE IF Z<-2.5 PLOT 85,X%,Y%
I% += 1
NEXT
NEXT J%
WAIT 1
*REFRESH
REM BBC SDL original uses C += 0.03 (slow in mini_basic); 0.5 matches user pace
C += 0.5
UNTIL FALSE
END
DATA 0, 1, T, -P, 2, R, P, 2, R, -1, Q, S, 1, Q, S
DATA 0, 1, -T, -P, 2, -R, P, 2, -R, -1, Q, -S, 1, Q, -S
DATA 0, -1, T, -P, -2, R, P, -2, R, -1, -Q, S, 1, -Q, S
DATA 0, -1, -T, -P, -2, -R, P, -2, -R, -1, -Q, -S, 1, -Q, -S
DATA 1, T, 0, 2, R, -P, 2, R, P, Q, S, -1, Q, S, 1
DATA 1, -T, 0, 2, -R, -P, 2, -R, P, Q, -S, -1, Q, -S, 1
DATA -1, T, 0, -2, R, -P, -2, R, P, -Q, S, -1, -Q, S, 1
DATA -1, -T, 0, -2, -R, -P, -2, -R, P, -Q, -S, -1, -Q, -S, 1
DATA T, 0, 1, R, -P, 2, R, P, 2, S, -1, Q, S, 1, Q
DATA T, 0, -1, R, -P, -2, R, P, -2, S, -1, -Q, S, 1, -Q
DATA -T, 0, 1, -R, -P, 2, -R, P, 2, -S, -1, Q, -S, 1, Q
DATA -T, 0, -1, -R, -P, -2, -R, P, -2, -S, -1, -Q, -S, 1, -Q
