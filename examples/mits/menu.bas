10 REM MITS-style menu using ON GOTO (Steve North / Creative Computing era)
20 PRINT "1 = Hello   2 = Square   3 = Quit"
30 PRINT "Choice";
31 INPUT C
40 ON C GOTO 100, 200, 300
50 PRINT "Bad choice"
60 GOTO 20
100 PRINT "Hello from menu"
110 GOTO 20
200 PRINT "N";
201 INPUT N
210 PRINT N; " squared = "; N * N
220 GOTO 20
300 END