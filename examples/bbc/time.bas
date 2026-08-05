REM BBC-style TIME demo (centiseconds) with REPEAT/UNTIL
REM TIME is a clock: read TIME, or assign TIME = 0 / TIME = n
TIME = 0
PRINT "Waiting 1 second..."
REPEAT
UNTIL TIME > 100
PRINT "TIME ="; TIME; " cs  ("; TIME / 100; " seconds)"
REM Optional: TIME = TIME + n adds n to the current reading (HELP SYSTEM)
TIME = TIME + 50
PRINT "After bumping by 50 cs:"; TIME