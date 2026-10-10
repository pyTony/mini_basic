REM mini superset - CLI program arguments (_argc, ARG, ARG$)

PRINT "Program arguments:"
PRINT "  _argc = "; _argc
IF _argc >= 1 THEN PRINT "  ARG(1)  = "; ARG(1)
IF _argc >= 1 THEN PRINT "  ARG$(1) = "; ARG$(1)
IF _argc >= 2 THEN PRINT "  ARG(2)  = "; ARG(2)
END