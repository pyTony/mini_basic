10 REM Analogue clock — wall time (TIME$), 12 o'clock at top
20 REM Same as examples/bbc/Clock.bas and basics/Clock.bas (working copy)
30 REM RIGHT$(TIME$,8) → HH:MM:SS with full BBC TIME$ or short form
40 REM Compare: jclock.bbc = mouse-following particle clock (different demo)
50 MODE 2
60 VDU 23,1,0;0;0;0;
70 REPEAT
80   T$ = TIME$
90   T$ = RIGHT$(T$,8)
100   HOUR24% = VAL(MID$(T$,1,2))
110   HOUR% = HOUR24% MOD 12
120   MINUTE% = VAL(MID$(T$,4,2))
130   SECOND% = VAL(MID$(T$,7,2))
140   GCOL 0,7
150   CIRCLE 640,512,300
160   FOR I% = 0 TO 11
170     A = RAD(90 - I% * 30)
180     MOVE 640 + COS(A) * 240,512 + SIN(A) * 240
190     DRAW 640 + COS(A) * 310,512 + SIN(A) * 310
200   NEXT
210   A = RAD(90 - HOUR% * 30 - MINUTE% * 0.5)
220   GCOL 0,1
230   MOVE 640,512: DRAW 640 + COS(A) * 110,512 + SIN(A) * 110
240   A = RAD(90 - MINUTE% * 6 - SECOND% * 0.1)
250   GCOL 0,2
260   MOVE 640,512: DRAW 640 + COS(A) * 190,512 + SIN(A) * 190
270   A = RAD(90 - SECOND% * 6)
280   GCOL 0,4
290   MOVE 640,512: DRAW 640 + COS(A) * 240,512 + SIN(A) * 240
300   COLOUR 7
310   PRINT TAB(2,1);"Analogue Clock"
320   PRINT TAB(6,2);HOUR24%;":";MINUTE%;":";SECOND%
330   WAIT 1
340 UNTIL FALSE
350 END
