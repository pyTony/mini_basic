10 REM Analogue clock — wall time (TIME$), 12 o'clock at top
20 REM Copied from basics/Clock.bas (working). RIGHT$(TIME$,8) → HH:MM:SS
30 REM even when TIME$ is full BBC "Day,dd Mon yyyy.hh:mm:ss"
40 REM *REFRESH removed (BBCSDL-only); works on mini_basic + other emulators
50 MODE 2
60 VDU 23,1,0;0;0;0;
70 REPEAT
80   REM CLS each frame optional — omit for less flicker
90   T$ = TIME$
100   T$ = RIGHT$(T$,8)
110   HOUR24% = VAL(MID$(T$,1,2))
120   HOUR% = HOUR24% MOD 12
130   MINUTE% = VAL(MID$(T$,4,2))
140   SECOND% = VAL(MID$(T$,7,2))
150   GCOL 0,7
160   CIRCLE 640,512,300
170   FOR I% = 0 TO 11
180     A = RAD(90 - I% * 30)
190     MOVE 640 + COS(A) * 240,512 + SIN(A) * 240
200     DRAW 640 + COS(A) * 310,512 + SIN(A) * 310
210   NEXT
220   A = RAD(90 - HOUR% * 30 - MINUTE% * 0.5)
230   GCOL 0,1
240   MOVE 640,512: DRAW 640 + COS(A) * 110,512 + SIN(A) * 110
250   A = RAD(90 - MINUTE% * 6 - SECOND% * 0.1)
260   GCOL 0,2
270   MOVE 640,512: DRAW 640 + COS(A) * 190,512 + SIN(A) * 190
280   A = RAD(90 - SECOND% * 6)
290   GCOL 0,4
300   MOVE 640,512: DRAW 640 + COS(A) * 240,512 + SIN(A) * 240
310   COLOUR 7
320   PRINT TAB(2,1);"Analogue Clock"
330   PRINT TAB(6,2);HOUR24%;":";MINUTE%;":";SECOND%
340   WAIT 1
350 UNTIL FALSE
360 END
