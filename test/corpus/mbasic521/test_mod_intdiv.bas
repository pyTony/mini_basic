10 REM Test MOD and Integer Division (\)
20 PRINT "Testing MOD and Integer Division"
30 PRINT "================================="
40 PRINT
50 REM Test 1: Basic MOD operation
60 PRINT "Test 1: Basic MOD"
70 PRINT "10 MOD 3 ="; 10 MOD 3; "(expected: 1)"
80 PRINT "17 MOD 5 ="; 17 MOD 5; "(expected: 2)"
90 PRINT "20 MOD 4 ="; 20 MOD 4; "(expected: 0)"
100 PRINT
110 REM Test 2: MOD with negative numbers
120 PRINT "Test 2: MOD with negatives"
130 PRINT "-10 MOD 3 ="; -10 MOD 3
140 PRINT "10 MOD -3 ="; 10 MOD -3
150 PRINT "-10 MOD -3 ="; -10 MOD -3
160 PRINT
170 REM Test 3: Basic integer division
180 PRINT "Test 3: Integer division (\)"
190 PRINT "10 \ 3 ="; 10 \ 3; "(expected: 3)"
200 PRINT "17 \ 5 ="; 17 \ 5; "(expected: 3)"
210 PRINT "20 \ 4 ="; 20 \ 4; "(expected: 5)"
220 PRINT "25 \ 7 ="; 25 \ 7; "(expected: 3)"
230 PRINT
240 REM Test 4: Integer division vs regular division
250 PRINT "Test 4: Integer div vs regular div"
260 PRINT "10 / 3 ="; 10 / 3; "(regular)"
270 PRINT "10 \ 3 ="; 10 \ 3; "(integer)"
280 PRINT "15 / 4 ="; 15 / 4; "(regular)"
290 PRINT "15 \ 4 ="; 15 \ 4; "(integer)"
300 PRINT
310 REM Test 5: Integer division with negatives
320 PRINT "Test 5: Integer div with negatives"
330 PRINT "-10 \ 3 ="; -10 \ 3
340 PRINT "10 \ -3 ="; 10 \ -3
350 PRINT "-10 \ -3 ="; -10 \ -3
360 PRINT
370 REM Test 6: MOD in expressions
380 PRINT "Test 6: MOD in expressions"
390 A = 100
400 B = 7
410 PRINT A; "MOD"; B; "="; A MOD B
420 C = (A MOD B) * 2
430 PRINT "Result * 2 ="; C
440 PRINT
450 REM Test 7: Integer division in expressions
460 PRINT "Test 7: Integer div in expressions"
470 X = 50
480 Y = 8
490 PRINT X; "\"; Y; "="; X \ Y
500 Z = (X \ Y) + 1
510 PRINT "Result + 1 ="; Z
520 PRINT
530 REM Test 8: MOD for even/odd check
540 PRINT "Test 8: Even/odd with MOD"
550 FOR I = 1 TO 10
560 IF I MOD 2 = 0 THEN PRINT I; "E"; ELSE PRINT I; "O";
570 NEXT I
580 PRINT
590 PRINT
600 REM Test 9: Combined operations
610 PRINT "Test 9: Combined MOD and \"
620 N = 47
630 PRINT N; "\ 10 ="; N \ 10; "(tens digit)"
640 PRINT N; "MOD 10 ="; N MOD 10; "(ones digit)"
650 PRINT
660 REM Test 10: Operator precedence
670 PRINT "Test 10: Precedence (MOD before +)"
680 PRINT "10 + 7 MOD 3 ="; 10 + 7 MOD 3; "(expected: 11)"
690 PRINT "10 + 5 \ 2 ="; 10 + 5 \ 2; "(expected: 12)"
700 PRINT
710 PRINT "MOD and integer division tests complete!"
720 END
