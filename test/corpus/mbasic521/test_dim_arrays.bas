10 REM Test DIM and Arrays
20 PRINT "Testing DIM and Arrays"
30 PRINT "======================"
40 PRINT
50 REM Test 1: Simple 1D array
60 PRINT "Test 1: 1D Array"
70 DIM A(5)
80 A(0) = 10
90 A(1) = 20
100 A(2) = 30
110 A(3) = 40
120 A(4) = 50
130 A(5) = 60
140 PRINT "  A(0) ="; A(0)
150 PRINT "  A(2) ="; A(2)
160 PRINT "  A(5) ="; A(5)
170 IF A(0) = 10 AND A(2) = 30 AND A(5) = 60 THEN PRINT "  PASS: 1D array works"
180 PRINT
190 REM Test 2: 2D array
200 PRINT "Test 2: 2D Array"
210 DIM B(3, 2)
220 B(0,0) = 1
230 B(1,1) = 5
240 B(2,2) = 9
250 B(3,0) = 13
260 PRINT "  B(0,0) ="; B(0,0)
270 PRINT "  B(1,1) ="; B(1,1)
280 PRINT "  B(2,2) ="; B(2,2)
290 PRINT "  B(3,0) ="; B(3,0)
300 IF B(0,0) = 1 AND B(1,1) = 5 AND B(2,2) = 9 THEN PRINT "  PASS: 2D array works"
310 PRINT
320 REM Test 3: String array
330 PRINT "Test 3: String Array"
340 DIM C$(3)
350 C$(0) = "RED"
360 C$(1) = "GREEN"
370 C$(2) = "BLUE"
380 C$(3) = "YELLOW"
390 PRINT "  C$(0) ="; C$(0)
400 PRINT "  C$(2) ="; C$(2)
410 IF C$(0) = "RED" AND C$(2) = "BLUE" THEN PRINT "  PASS: String array works"
420 PRINT
430 REM Test 4: Array with FOR loop
440 PRINT "Test 4: Array with FOR loop"
450 DIM D(4)
460 FOR I = 0 TO 4
470   D(I) = I * 10
480 NEXT I
490 PRINT "  D(0) ="; D(0)
500 PRINT "  D(2) ="; D(2)
510 PRINT "  D(4) ="; D(4)
520 IF D(0) = 0 AND D(2) = 20 AND D(4) = 40 THEN PRINT "  PASS: FOR loop with array works"
530 PRINT
540 PRINT "All array tests complete!"
550 END
