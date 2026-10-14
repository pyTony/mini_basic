REM first real SOUND/PLAY call mid-game (that was causing a multi-second
REM breakout.bas -- paddle/ball/bricks, showcasing graphics + SOUND together
REM Controls: LEFT/RIGHT arrows move the paddle, SPACE starts/serves.
REM Each brick row has its own pitch; breaking a brick, hitting the paddle
REM and hitting a wall each play their own sampled effect (via *PLAY),
REM alongside the synthesized per-row SOUND tone on a brick break; a short
REM arpeggio plays on winning or losing the game. *MUSIC loops a background
REM track for the whole game (line 95), stopped once on game-over (PROCgameend).
REM Line 15's silent SOUND call warms up the audio engine during the title
REM screen, rather than taking the one-time pygame/mixer init cost on the
REM stall and visible ball "hesitation"/rewind right at the first paddle hit).
REM Line 85's CLS clears the title text off the text/VDU layer before play
REM starts -- CLG in the main loop only clears the graphics layer, so the
REM title stayed on screen, overlaid on the game, for the rest of the run.
REM The playfield is narrower than the full screen so the paddle crosses it
REM quickly without a higher per-frame speed; PROCdrawsidepanels fills the
REM resulting side margins with a solid colour (palette slot 6, otherwise
REM unused by the brick rows) instead of leaving them black, and the score
REM and lives counters are printed inside those margins rather than across
REM the top of the playfield, so neither overlaps the side walls.
REM Panels/walls are static, so they're drawn once in PROCinit, not per
REM frame: a redefined-palette (truecolour) fill is much slower per pixel
REM than a standard-palette one, and redrawing the two full-height panels
REM 20x/second made the game crawl. The main loop instead clears only the
REM playfield rectangle each frame (GCOL 0, never redefined, so it stays
REM on the fast fill path) and leaves the panels/walls untouched under it.MODE 8
SOUND 0,0,0,0
*REFRESH OFF
COLOUR 7
CLS
*DISPLAY "logo.png" 260,780,760,116
PRINT TAB(10,13)"Arrows move, SPACE serves"
PRINT TAB(13,15)"Press SPACE to start"
*REFRESH
REPEAT UNTIL INKEY(-99)
CLS
PROCinit
*MUSIC "music.mp3",20
playing% = TRUE
REPEAT
    t% = TIME
    GCOL 0: RECTANGLE FILL fx0%, 0, fw%, sh%
    PROCdrawbricks
    PROCmovepaddle
    PROCdrawpaddle
    IF served% THEN PROCmoveball ELSE PROCserveball
    PROCdrawball
    PROCdrawhud
    *REFRESH
REPEAT WAIT 0: UNTIL TIME <> t%
    IF lives% <= 0 OR bricksleft% <= 0 THEN playing% = FALSE
UNTIL NOT playing%
PROCgameend
REPEAT WAIT 1: UNTIL FALSE
END
DEF PROCinit
    sw% = 1280: sh% = 1024
    COLOUR 6,18,18,46
    fx0% = 260: fw% = 760: fx1% = fx0% + fw%
    cols% = 8: rows% = 5
    DIM brick(cols%-1, rows%-1)
    FOR r% = 0 TO rows%-1
        FOR c% = 0 TO cols%-1
            brick(c%,r%) = 1
        NEXT c%
    NEXT r%
    bricksleft% = cols% * rows%
    bw% = 83: bh% = 32: gap% = 8
    bx0% = fx0% + 20: by0% = 920
    pw% = 120: ph% = 20: py% = 60
    px% = fx0% + fw%/2 - pw%/2
    br% = 10
    score% = 0: lives% = 3
    speedmul% = 180: ballsubsteps% = 2
    served% = FALSE
    PROCdrawsidepanels
    PROCdrawwalls
ENDPROC
DEF PROCserveball
    ballx% = px% + pw%/2
    bally% = py% + ph% + br%
    IF INKEY(-99) THEN ballvx% = 16 * speedmul% / 100 : ballvy% = 20 * speedmul% / 100 : served% = TRUE
ENDPROC
DEF PROCmovepaddle
    IF INKEY(-26) THEN px% -= 28
    IF INKEY(-122) THEN px% += 28
    IF px% < fx0% THEN px% = fx0%
    IF px% > fx1% - pw% THEN px% = fx1% - pw%
ENDPROC
DEF PROCmoveball
    LOCAL i%, stepvx%, stepvy%
    stepvx% = ballvx% / ballsubsteps%: stepvy% = ballvy% / ballsubsteps%
    FOR i% = 1 TO ballsubsteps%
        GCOL 0: RECTANGLE FILL ballx%-br%, bally%-br%, br%*2, br%*2
        ballx% += stepvx%: bally% += stepvy%
        IF ballx% - br% <= fx0% THEN ballx% = fx0%+br% : ballvx% = -ballvx% : stepvx% = -stepvx% : *PLAY"sfx_wall.wav",2
        IF ballx% + br% >= fx1% THEN ballx% = fx1%-br% : ballvx% = -ballvx% : stepvx% = -stepvx% : *PLAY"sfx_wall.wav",2
        IF bally% + br% >= sh% THEN bally% = sh%-br% : ballvy% = -ballvy% : stepvy% = -stepvy% : *PLAY"sfx_wall.wav",2
        IF bally% - br% <= py% + ph% AND bally% >= py% - 30 AND ballx% >= px% AND ballx% <= px%+pw% AND ballvy% < 0 THEN PROCpaddlehit : stepvx% = ballvx% / ballsubsteps% : stepvy% = ballvy% / ballsubsteps%
        IF bally% + br% < 0 THEN PROClifelost
        PROCcheckbricks
        PROCdrawball
        *REFRESH
    NEXT i%
ENDPROC
DEF PROCpaddlehit
    ballvy% = -ballvy%
    hitpos% = (ballx% - px%) - pw%/2
    ballvx% = hitpos% * 9 * speedmul% / 4000
    IF ballvx% = 0 THEN ballvx% = 9 * speedmul% / 100
    *PLAY "sfx_hit.wav",1
ENDPROC
DEF PROClifelost
    lives% -= 1
    served% = FALSE
    SOUND 1,-6,24,20
ENDPROC
DEF PROCcheckbricks
    LOCAL c%, r%, bxc%, byc%
    FOR r% = 0 TO rows%-1
        FOR c% = 0 TO cols%-1
            IF brick(c%,r%) = 1 THEN
                bxc% = bx0% + c%*(bw%+gap%)
                byc% = by0% - r%*(bh%+gap%)
                IF ballx%+br% >= bxc% AND ballx%-br% <= bxc%+bw% AND bally%+br% >= byc% AND bally%-br% <= byc%+bh% THEN
                    brick(c%,r%) = 0
                    bricksleft% -= 1
                    score% += (rows% - r%) * 10
                    ballvy% = -ballvy%
                    SOUND 2,-8,60 + (rows%-1 - r%) * 15,4
                    *PLAY "sfx_break.wav",3
                ENDIF
            ENDIF
        NEXT c%
    NEXT r%
ENDPROC
DEF PROCdrawsidepanels
    GCOL 6
    RECTANGLE FILL 0, 0, fx0%-10, sh%
    RECTANGLE FILL fx1%+10, 0, sw%-(fx1%+10), sh%
ENDPROC
DEF PROCdrawwalls
    GCOL 7
    RECTANGLE FILL fx0%-10, 0, 6, sh%
    RECTANGLE FILL fx1%+4, 0, 6, sh%
ENDPROC
DEF PROCdrawbricks
    LOCAL c%, r%
    FOR r% = 0 TO rows%-1
        FOR c% = 0 TO cols%-1
            IF brick(c%,r%) = 1 THEN
                *DISPLAY "brick.png" bx0%+c%*(bw%+gap%), by0%-r%*(bh%+gap%), bw%, bh%
            ENDIF
        NEXT c%
    NEXT r%
ENDPROC
DEF PROCdrawpaddle
    GCOL 7
    RECTANGLE FILL px%, py%, pw%, ph%
ENDPROC
DEF PROCdrawball
    *DISPLAY "ball.png" ballx%-br%, bally%-br%, br%*2, br%*2
ENDPROC
DEF PROCdrawhud
    COLOUR 7
    PRINT TAB(1,0)"Score"
    PRINT TAB(1,1); score%;"   "
    PRINT TAB(66,0)"Lives"
    PRINT TAB(66,1); lives%;" "
ENDPROC
DEF PROCgameend
    CLG
    *MUSIC OFF
    COLOUR 7
    IF bricksleft% <= 0 THEN
        PRINT TAB(16,12)"YOU WIN!"
        FOR n% = 0 TO 7
            SOUND 1,-8,53 + n%*4,5
        NEXT n%
    ELSE
        PRINT TAB(14,12)"GAME OVER"
        FOR n% = 7 TO 0 STEP -1
            SOUND 1,-8,40 + n%*4,5
        NEXT n%
    ENDIF
    PRINT TAB(12,14)"Final score "; score%
    *REFRESH
ENDPROC

