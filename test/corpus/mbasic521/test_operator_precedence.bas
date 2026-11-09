10 REM Test operator precedence in MBASIC 5.21
20 REM Each test computes a result and checks if it matches expected value
30 PRINT "Operator Precedence Tests"
40 PRINT "========================="
50 PRINT
60 PASSED = 0
70 FAILED = 0
80 REM
90 REM Test 1: Multiplication before addition
100 RESULT = 3*3+1
110 EXPECTED = 10
120 GOSUB 1200
130 REM
140 REM Test 2: Division before subtraction
150 RESULT = 10-8/2
160 EXPECTED = 6
170 GOSUB 1200
180 REM
190 REM Test 3: Exponentiation before multiplication
200 RESULT = 2*3^2
210 EXPECTED = 18
220 GOSUB 1200
230 REM
240 REM Test 4: Multiplication before addition (reversed)
250 RESULT = 1+3*3
260 EXPECTED = 10
270 GOSUB 1200
280 REM
290 REM Test 5: Multiple operations
300 RESULT = 2+3*4-5
310 EXPECTED = 9
320 GOSUB 1200
330 REM
340 REM Test 6: Exponentiation before division
350 RESULT = 16/2^2
360 EXPECTED = 4
370 GOSUB 1200
380 REM
390 REM Test 7: Integer division before addition
400 RESULT = 10\3+1
410 EXPECTED = 4
420 GOSUB 1200
430 REM
440 REM Test 8: MOD before addition
450 RESULT = 10 MOD 3+1
460 EXPECTED = 2
470 GOSUB 1200
480 REM
490 REM Test 9: Negation before multiplication
500 RESULT = -2*3
510 EXPECTED = -6
520 GOSUB 1200
530 REM
540 REM Test 10: Exponentiation before negation
550 RESULT = -2^2
560 EXPECTED = -4
570 GOSUB 1200
580 REM
590 REM Test 11: Multiplication and division left to right
600 RESULT = 12/2*3
610 EXPECTED = 18
620 GOSUB 1200
630 REM
640 REM Test 12: Addition and subtraction left to right
650 RESULT = 10-3+2
660 EXPECTED = 9
670 GOSUB 1200
680 REM
690 REM Test 13: Integer division before MOD
700 RESULT = 10\3 MOD 2
710 EXPECTED = 1
720 GOSUB 1200
730 REM
740 REM Test 14: Relational after arithmetic
750 RESULT = 3+2>4
760 EXPECTED = -1
770 GOSUB 1200
780 REM
790 REM Test 15: AND after relational
800 RESULT = 1=1 AND 2=2
810 EXPECTED = -1
820 GOSUB 1200
830 REM
840 REM Test 16: OR after AND
850 RESULT = 0 OR 1 AND 0
860 EXPECTED = 0
870 GOSUB 1200
880 REM
890 REM Test 17: NOT before AND
900 RESULT = NOT 0 AND 1
910 EXPECTED = 1
920 GOSUB 1200
930 REM
940 REM Test 18: Complex arithmetic
950 RESULT = 2+3*4^2-10/5
960 EXPECTED = 48
970 GOSUB 1200
980 REM
990 REM Test 19: Mixed division types
1000 RESULT = 10/4*2
1010 EXPECTED = 5
1020 GOSUB 1200
1030 REM
1040 REM Test 20: Parentheses override
1050 RESULT = (3+1)*3
1060 EXPECTED = 12
1070 GOSUB 1200
1080 REM
1090 REM Print summary
1100 PRINT
1110 PRINT "========================="
1120 PRINT "Tests passed:";PASSED
1130 PRINT "Tests failed:";FAILED
1140 IF FAILED = 0 THEN PRINT "All tests PASSED!" ELSE PRINT "Some tests FAILED!"
1150 END
1160 REM
1170 REM Subroutine to check result at line 1200
1180 REM
1190 REM
1200 IF RESULT = EXPECTED THEN PRINT "PASS: Got";RESULT;"as expected" : PASSED = PASSED + 1 : RETURN
1210 PRINT "FAIL: Expected";EXPECTED;"but got";RESULT
1220 FAILED = FAILED + 1
1230 RETURN
