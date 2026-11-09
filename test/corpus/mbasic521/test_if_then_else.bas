10 REM Test IF/THEN/ELSE Statement
20 PRINT "Testing IF/THEN/ELSE"
30 PRINT "==================="
40 PRINT
50 REM Test 1: Simple IF/THEN
60 PRINT "Test 1: Simple IF/THEN"
70 A = 10
80 IF A = 10 THEN PRINT "  PASS: A equals 10"
90 IF A = 5 THEN PRINT "  FAIL: A should not equal 5"
100 PRINT
110 REM Test 2: IF/THEN/ELSE
120 PRINT "Test 2: IF/THEN/ELSE"
130 B = 20
140 IF B > 15 THEN PRINT "  PASS: B > 15" ELSE PRINT "  FAIL: B should be > 15"
150 IF B < 15 THEN PRINT "  FAIL: B should not be < 15" ELSE PRINT "  PASS: B not < 15"
160 PRINT
170 REM Test 3: Comparison operators
180 PRINT "Test 3: Comparison operators"
190 X = 5
200 Y = 10
210 IF X < Y THEN PRINT "  PASS: 5 < 10"
220 IF X > Y THEN PRINT "  FAIL: 5 should not be > 10"
230 IF X <= 5 THEN PRINT "  PASS: 5 <= 5"
240 IF X >= 5 THEN PRINT "  PASS: 5 >= 5"
250 IF X <> Y THEN PRINT "  PASS: 5 <> 10"
260 IF X = Y THEN PRINT "  FAIL: 5 should not equal 10"
270 PRINT
280 REM Test 4: String comparisons
290 PRINT "Test 4: String comparisons"
300 A$ = "HELLO"
310 B$ = "WORLD"
320 IF A$ = "HELLO" THEN PRINT "  PASS: String equality"
330 IF A$ <> B$ THEN PRINT "  PASS: String inequality"
340 IF A$ < B$ THEN PRINT "  PASS: HELLO < WORLD (alphabetically)"
350 PRINT
360 REM Test 5: Logical AND
370 PRINT "Test 5: Logical AND"
380 C = 15
390 IF C > 10 AND C < 20 THEN PRINT "  PASS: 10 < 15 < 20"
400 IF C > 20 AND C < 30 THEN PRINT "  FAIL: Should not pass"
410 PRINT
420 REM Test 6: Logical OR
430 PRINT "Test 6: Logical OR"
440 D = 5
450 IF D = 5 OR D = 10 THEN PRINT "  PASS: D is 5 or 10"
460 IF D = 3 OR D = 7 THEN PRINT "  FAIL: D should not be 3 or 7"
470 PRINT
480 REM Test 7: NOT operator
490 PRINT "Test 7: NOT operator"
500 E = 0
510 IF NOT E THEN PRINT "  PASS: NOT 0 is true"
520 E = 1
530 IF NOT E THEN PRINT "  FAIL: NOT 1 should be false"
540 PRINT
550 REM Test 8: Nested IF statements
560 PRINT "Test 8: Nested IF"
570 F = 25
580 IF F > 20 THEN IF F < 30 THEN PRINT "  PASS: Nested IF works (20 < 25 < 30)"
590 PRINT
600 PRINT "All IF/THEN/ELSE tests complete!"
610 END
