   10 REM BBC graphics demo — run: mini_basic --pygame examples/mini/bbc_graphics_demo.bas
   15 REM Uses BBC MODE/PLOT commands; default mini dialect (numbered lines)
   20 MODE 1
   30 VDU 29,160;128;
   40 CLG
   50 REM Large cyan circle (right side, drawn first)
   60 GCOL 0,6
   70 MOVE 220,128
   80 PLOT 156,275,128
   90 REM Green rectangle outline (upper left)
  100 GCOL 0,2
  110 MOVE 35,195
  120 DRAW 90,0
  130 DRAW 0,-85
  140 DRAW -90,0
  150 DRAW 0,85
  160 REM Red filled triangle (inside the green square)
  170 GCOL 0,1
  180 MOVE 58,180
  190 MOVE 108,140
  200 PLOT 85,58,140
  210 REM Small red filled circle (lower left)
  220 MOVE 70,70
  230 PLOT 156,95,50
  240 REM Caption in graphics mode (MODE 8 would clear the screen)
  250 COLOUR 11
  260 PRINT TAB(6,22);"bbc_graphics_demo"
  270 END