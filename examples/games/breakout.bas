    1 REM dialect: bbc
   10 MODE 8
   15 SOUND 0,0,0,0
   20 *REFRESH OFF
   30 COLOUR 7
   40 CLS
   50 *DISPLAY "examples/games/logo.png" 260,780,760,116
   60 PRINT TAB(10,13)"Arrows move, SPACE serves"
   70 PRINT TAB(13,15)"Press SPACE to start"
   75 *REFRESH
   80 REPEAT UNTIL INKEY(-99)
   85 CLS
   90 PROCinit
   95 *MUSIC "examples/games/Sudden_Death_Volley.mp3",20
  100 playing% = TRUE
  110 REPEAT
  120   t% = TIME
  130   GCOL 0: RECTANGLE FILL fx0%, 0, fw%, sh%
  140   PROCdrawbricks
  150   PROCmovepaddle
  160   IF served% THEN PROCmoveball ELSE PROCserveball
  170   PROCdrawpaddle
  180   PROCdrawball
  190   PROCdrawhud
  200   *REFRESH
  210   REPEAT WAIT 0: UNTIL TIME <> t%
  220   IF lives% <= 0 OR bricksleft% <= 0 THEN playing% = FALSE
  230 UNTIL NOT playing%
  240 PROCgameend
  250 REPEAT WAIT 1: UNTIL FALSE
  260 END
  270
  280 DEF PROCinit
  282 sw% = 1280: sh% = 1024
  284 COLOUR 6,18,18,46
  285 fx0% = 260: fw% = 760: fx1% = fx0% + fw%
  290 cols% = 8: rows% = 5
  300 DIM brick(cols%-1, rows%-1)
  310 FOR r% = 0 TO rows%-1
  320   FOR c% = 0 TO cols%-1
  330     brick(c%,r%) = 1
  340   NEXT c%
  350 NEXT r%
  360 bricksleft% = cols% *rows%
  370 bw% = 83: bh% = 32: gap% = 8
  380 bx0% = fx0% + 20: by0% = 920
  390 pw% = 120: ph% = 20: py% = 60
  400 px% = fx0% + fw%/2 - pw%/2
  410 br% = 10
  420 score% = 0: lives% = 3
  430 served% = FALSE
  435 PROCdrawsidepanels
  436 PROCdrawwalls
  440 ENDPROC
  450
  460 DEF PROCserveball
  470 ballx% = px% + pw%/2
  480 bally% = py% + ph% + br%
  490 IF INKEY(-99) THEN ballvx% = 16 : ballvy% = 20 : served% = TRUE
  500 ENDPROC
  510
  520 DEF PROCmovepaddle
  530 IF INKEY(-26) THEN px% -= 28
  540 IF INKEY(-122) THEN px% += 28
  550 IF px% < fx0% THEN px% = fx0%
  560 IF px% > fx1% - pw% THEN px% = fx1% - pw%
  570 ENDPROC
  580
  590 DEF PROCmoveball
  600 ballx% += ballvx%: bally% += ballvy%
  610 IF ballx% - br% <= fx0% THEN ballx% = fx0%+br% : ballvx% = -ballvx% : *PLAY"examples/games/sfx_wall.wav",2
  620 IF ballx% + br% >= fx1% THEN ballx% = fx1%-br% : ballvx% = -ballvx% : *PLAY"examples/games/sfx_wall.wav",2
  630 IF bally% + br% >= sh% THEN bally% = sh%-br% : ballvy% = -ballvy% : *PLAY"examples/games/sfx_wall.wav",2
  640 IF bally% - br% <= py% + ph% AND bally% >= py% - 30 AND ballx% >= px% AND ballx% <= px%+pw% AND ballvy% < 0 THEN PROCpaddlehit
  650 IF bally% + br% < 0 THEN PROClifelost
  660 PROCcheckbricks
  670 ENDPROC
  680
  690 DEF PROCpaddlehit
  700 ballvy% = -ballvy%
  710 hitpos% = (ballx% - px%) - pw%/2
  720 ballvx% = hitpos% * 9 / 40
  730 IF ballvx% = 0 THEN ballvx% = 9
  740 *PLAY "examples/games/sfx_hit.wav",1
  750 ENDPROC
  760
  770 DEF PROClifelost
  780 lives% -= 1
  790 served% = FALSE
  800 SOUND 1,-6,24,20
  810 ENDPROC
  820
  830 DEF PROCcheckbricks
  840 LOCAL c%, r%, bxc%, byc%
  850 FOR r% = 0 TO rows%-1
  860   FOR c% = 0 TO cols%-1
  870     IF brick(c%,r%) = 1 THEN
  880       bxc% = bx0% + c%*(bw%+gap%)
  890       byc% = by0% - r%*(bh%+gap%)
  900       IF ballx%+br% >= bxc% AND ballx%-br% <= bxc%+bw% AND bally%+br% >= byc% AND bally%-br% <= byc%+bh% THEN
  910         brick(c%,r%) = 0
  920         bricksleft% -= 1
  930         score% += (rows% - r%) *10
  940         ballvy% = -ballvy%
  950         SOUND 2,-8,60 + (rows%-1 - r%) *15,4
  955         *PLAY "examples/games/sfx_break.wav",3
  960       ENDIF
  970     ENDIF
  980   NEXT c%
  990 NEXT r%
 1000 ENDPROC
 1010
 1011 DEF PROCdrawsidepanels
 1012 GCOL 6
 1013 RECTANGLE FILL 0, 0, fx0%-10, sh%
 1014 RECTANGLE FILL fx1%+10, 0, sw%-(fx1%+10), sh%
 1015 ENDPROC
 1016
 1020 DEF PROCdrawwalls
 1021 GCOL 7
 1022 RECTANGLE FILL fx0%-10, 0, 6, sh%
 1023 RECTANGLE FILL fx1%+4, 0, 6, sh%
 1024 ENDPROC
 1025
 1026 DEF PROCdrawbricks
 1030 LOCAL c%, r%
 1040 FOR r% = 0 TO rows%-1
 1060   FOR c% = 0 TO cols%-1
 1070     IF brick(c%,r%) = 1 THEN
 1071       *DISPLAY "examples/games/brick.png" bx0%+c%*(bw%+gap%), by0%-r%*(bh%+gap%), bw%, bh%
 1072     ENDIF
 1080   NEXT c%
 1090 NEXT r%
 1100 ENDPROC
 1110
 1120 DEF PROCdrawpaddle
 1130 GCOL 7
 1140 RECTANGLE FILL px%, py%, pw%, ph%
 1150 ENDPROC
 1160
 1170 DEF PROCdrawball
 1190 *DISPLAY "examples/games/ball.png" ballx%-br%, bally%-br%, br%*2, br%*2
 1200 ENDPROC
 1210
 1220 DEF PROCdrawhud
 1230 COLOUR 7
 1232 PRINT TAB(1,0)"Score"
 1234 PRINT TAB(1,1); score%;"   "
 1236 PRINT TAB(66,0)"Lives"
 1238 PRINT TAB(66,1); lives%;" "
 1250 ENDPROC
 1260
 1270 DEF PROCgameend
 1280 CLG
 1285 *MUSIC OFF
 1290 COLOUR 7
 1300 IF bricksleft% <= 0 THEN
 1310   PRINT TAB(16,12)"YOU WIN!"
 1320   FOR n% = 0 TO 7
 1330     SOUND 1,-8,53 + n%*4,5
 1340   NEXT n%
 1350 ELSE
 1360   PRINT TAB(14,12)"GAME OVER"
 1370   FOR n% = 7 TO 0 STEP -1
 1380     SOUND 1,-8,40 + n%*4,5
 1390   NEXT n%
 1400 ENDIF
 1410 PRINT TAB(12,14)"Final score "; score%
 1420 *REFRESH
 1430 ENDPROC
 1431 REM stall and visible ball "hesitation"/rewind right at the first paddle hit).
 1432 REM Line 85's CLS clears the title text off the text/VDU layer before play
 1433 REM starts -- CLG in the main loop only clears the graphics layer, so the
 1434 REM title stayed on screen, overlaid on the game, for the rest of the run.
 1435 REM The playfield is narrower than the full screen so the paddle crosses it
 1436 REM quickly without a higher per-frame speed; PROCdrawsidepanels fills the
 1437 REM resulting side margins with a solid colour (palette slot 6, otherwise
 1438 REM unused by the brick rows) instead of leaving them black, and the score
 1439 REM and lives counters are printed inside those margins rather than across
 1440 REM the top of the playfield, so neither overlaps the side walls.
 1441 REM Panels/walls are static, so they're drawn once in PROCinit, not per
 1442 REM frame: a redefined-palette (truecolour) fill is much slower per pixel
 1443 REM than a standard-palette one, and redrawing the two full-height panels
 1444 REM 20x/second made the game crawl. The main loop instead clears only the
 1445 REM playfield rectangle each frame (GCOL 0, never redefined, so it stays
 1446 REM on the fast fill path) and leaves the panels/walls untouched under it.
 1450 REM first real SOUND/PLAY call mid-game (that was causing a multi-second
 1451 REM breakout.bbc -- paddle/ball/bricks, showcasing graphics + SOUND together
 1452 REM Controls: LEFT/RIGHT arrows move the paddle, SPACE starts/serves.
 1453 REM Each brick row has its own pitch; breaking a brick, hitting the paddle
 1454 REM and hitting a wall each play their own sampled effect (via *PLAY),
 1455 REM alongside the synthesized per-row SOUND tone on a brick break; a short
 1456 REM arpeggio plays on winning or losing the game. *MUSIC loops a background
 1457 REM track for the whole game (line 95), stopped once on game-over (PROCgameend).
 1458 REM Line 15's silent SOUND call warms up the audio engine during the title
 1459 REM screen, rather than taking the one-time pygame/mixer init cost on the