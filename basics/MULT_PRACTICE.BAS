     5 REPEAT
    10 n% = RND(10)
    20 m% = RND(10)
    30 PRINT "What is "; n%" * "; m%;
    40 INPUT ans%
    45 IF ans% = 0 END
    50 IF ans% = n%* m% THEN
    60   PRINT "Well done"
    70 ELSE
    80   PRINT "Wrong"
    90   PRINT n%;" * "; m%" = "; n%* m%
   100 ENDIF
   110 UNTIL FALSE
