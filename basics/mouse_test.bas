    10 MODE 8
    20 REPEAT
    30   MOUSE X%, Y%, B%
    40   *REFRESH
    50   IF (B% AND 1) <> 0 THEN
    60     PRINT TAB(0,0);"*** LEFT CLICKED  ***"
    70   ELIF (B% AND 2) <> 0 THEN
    80     PRINT TAB(0,0);"*** RIGHT CLICKED ***"
    90   ELIF (B% AND 4) <> 0 THEN
   100     PRINT TAB(0,0);"*** WHEEL CLICKED ***"
   110   ELSE
   120     PRINT TAB(0,0);"                     "
   130   ENDIF
   140   *REFRESH
   150   WAIT 1
   160 UNTIL FALSE
