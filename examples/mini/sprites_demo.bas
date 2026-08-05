   10 REM Animated sprite demo — run: mini_basic --pygame examples/mini/sprites_demo.bas
   20 MODE 1
   30 VDU 29,160;128;
   40 CLG
   50 REM 8x8 ship sprite (-1 = transparent)
   60 SPRITEDEF 1,8,8,-1,-1,2,2,-1,-1,-1,-1,-1,-1,2,2,2,2,-1,-1,-1,2,2,7,2,7,2,2,-1,2,2,2,2,2,2,2,-1,-1,-1,2,2,2,-1,-1,-1,-1,-1,2,2,-1,-1,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1
   70 REM 8x8 invader sprite
   80 SPRITEDEF 2,8,8,-1,-1,1,1,1,1,-1,-1,-1,1,1,1,1,1,1,-1,1,1,7,1,1,7,1,1,1,1,1,1,1,1,1,1,-1,1,1,-1,-1,1,1,-1,-1,1,1,-1,-1,1,1,-1,1,1,-1,-1,-1,-1,1,1,1,-1,-1,-1,-1,-1,-1,1
   90 COLOUR 11
  100 PRINT TAB(8,22);"sprites_demo"
  110 REM One line per frame avoids flicker (all draws, then one refresh)
  120 FOR X=0 TO 280 STEP 3
  130   CLG : GCOL 0,7 : PLOT 69,40,40 : PLOT 69,120,60 : PLOT 69,250,45 : PLOT 69,180,90 : PLOT 69,70,150 : SPRITE 1,X,40 : SPRITE 2,280-X,120 : WAIT 3
  140 NEXT X
  150 END