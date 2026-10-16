REM BBC-style structured menu (GOTO available in BBC BASIC; this avoids it)
REM Same choices as examples/mits/menu.bas

WHILE 1
  PRINT "1 = Hello   2 = Square   3 = Quit"
  PRINT "Choice";
  INPUT C
  IF C = 1 THEN
    PRINT "Hello from menu"
  ELSEIF C = 2 THEN
    PRINT "N";
    INPUT N
    PRINT N; " squared = "; N * N
  ELSEIF C = 3 THEN
    END
  ELSE
    PRINT "Bad choice"
  ENDIF
WEND