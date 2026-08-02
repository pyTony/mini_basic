REM FPS bench: soccerball cost (12 pentagons / PLOT 85).
REM Long enough for a full spin so we do not stop on an edge-on "line" face.
REM Live FPS every frame on the ball; final summary in text.
MODE 9: OFF
ORIGIN 640,512: COLOUR 130
DIM XYZ(2,59), TMP(2,59), B(2,2), C(2,2)
S = SQR(5) + 1: P = S / 2: Q = P + 2: R = S + 1: T = P * 3
FOR I% = 0 TO 59
  READ XYZ(0,I%), XYZ(1,I%), XYZ(2,I%)
NEXT
B = 0.5: ang = 0
B() = COS(B), 0, -SIN(B), 0, 1, 0, SIN(B), 0, COS(B)
REM ~full turn: 2*PI/0.03 ≈ 210; use 240 frames for margin
Nframes% = 240
*REFRESH OFF
t0 = TIME
FOR frames% = 1 TO Nframes%
  C() = COS(ang), SIN(ang), 0, -SIN(ang), COS(ang), 0, 0, 0, 1
  C() = B() . C(): TMP() = C() . XYZ()
  CLS
  GCOL 3: CIRCLE FILL 0, 0, 432: GCOL 0
  I% = 0
  FOR J% = 0 TO 11
    Z = SUM(TMP(1, I% TO I% + 4))
    FOR K% = 0 TO 4
      X% = 3200 * TMP(0,I%) / (36 + TMP(1,I%))
      Y% = 3200 * TMP(2,I%) / (36 + TMP(1,I%))
      IF K% < 2 MOVE X%,Y% ELSE IF Z < -2.5 PLOT 85,X%,Y%
      I% += 1
    NEXT
  NEXT J%
  elapsed = (TIME - t0) / 100
  REM Clean HUD (not PLOT 85 — that made a pointed black blob over the ball)
  GCOL 0,0
  RECTANGLE FILL -200, -10, 400, 70
  GCOL 0,7
  VDU 5
  MOVE -180, 40
  IF elapsed > 0 THEN PRINT frames%; "/"; Nframes%; " "; INT(frames% / elapsed); " fps" ELSE PRINT frames%; "/"; Nframes%; " ..."
  VDU 4
  *REFRESH
  ang += 0.03
NEXT
elapsed = (TIME - t0) / 100
VDU 4
IF elapsed > 0 THEN PRINT "Done: "; Nframes%; " frames, "; INT(Nframes% / elapsed); " fps" ELSE PRINT "Done: n/a"
*REFRESH
WAIT 300
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
