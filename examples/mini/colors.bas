REM mini superset - ANSI FG$/BG$ (color on spaces only)

PRINT "ANSI color strip (mini mode):"
FOR I = 16 TO 21
  PRINT RESET$(); BG$(I); FG$(I); " ";
NEXT I
PRINT RESET$()
END