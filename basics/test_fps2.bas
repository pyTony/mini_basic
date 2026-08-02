REM Continuous FPS monitor (yellow disc).
REM WAIT 50 was 50 cs = 0.5 s/frame (~2 fps max) and looked "broken".
REM No wait here — *REFRESH only; FPS is true present rate.
REM VDU 5 puts the counter on the ball (PRINT TAB is text-layer only).
MODE 9
ORIGIN 640,512
*REFRESH OFF
t = TIME
frames% = 0
REPEAT
  CLS
  GCOL 3 : CIRCLE FILL 0,0,400 : GCOL 0
  frames% += 1
  elapsed = (TIME - t) / 100
  VDU 5
  MOVE -200, 40
  IF elapsed > 0 THEN PRINT INT(frames% / elapsed); " fps   " ELSE PRINT "...    "
  VDU 4
  *REFRESH
UNTIL FALSE
