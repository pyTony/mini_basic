REM sound_demo.bbc -- mini_basic SOUND showcase
REM Plays a short ascending scale on channel 1, a bass note on channel 2,
REM and a noise "hi-hat" on channel 0 (the traditional BBC noise channel).
REM Approximate tone synthesis via pygame -- see mini_basic/sound.py.
10 MODE 8
20 COLOUR 7
30 CLS
40 PRINT "SOUND demo -- scale + bass + hi-hat"
50 PRINT
60 DIM scale(7)
70 FOR i% = 0 TO 7
80   scale(i%) = 53 + i% * 8
90 NEXT i%
100 FOR i% = 0 TO 7
110   PRINT "note "; i% + 1
120   SOUND 1, -8, scale(i%), 6
130   SOUND 0, -12, 100, 2
140   IF (i% MOD 2) = 0 THEN SOUND 2, -6, scale(i%) - 24, 6
150 NEXT i%
160 PRINT
170 PRINT "done."
