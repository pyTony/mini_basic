    10 REM Better ANSI color test - visible characters
    20 FOR I = 0 TO 15
    30   PRINT RGB$(rnd(255), rnd(256), rnd(255));"#";
    40 NEXT I
    50 PRINT RESET$;RGB$(255,255,255)
    60 PRINT "Done"
    70 END
