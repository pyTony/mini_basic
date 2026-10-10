   10 REM Find machine epsilon the classic way (1+eps until 1+eps=1)
   20 REM Compare with interpreter pseudo-variable _epsilon
   30 E = 1
   40 WHILE 1 + E <> 1
   50 E = E / 2
   60 WEND
   65 REM Loop stops one step past the last distinguishable value
   66 E = E * 2
   70 PRINT "Found by loop: "; E
   80 PRINT "Interpreter  : "; _epsilon
   90 IF E = _epsilon THEN PRINT "Match!" ELSE PRINT "Differ"
  100 END