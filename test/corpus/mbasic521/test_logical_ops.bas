10 REM Test Logical Operators
20 REM Note: In MBASIC, TRUE = -1 and FALSE = 0
30 PRINT "Testing Logical Operators"
40 PRINT "========================="
50 PRINT
60 REM Test 1: AND operator
70 PRINT "Test 1: AND operator"
80 PRINT "-1 AND -1 ="; -1 AND -1; "(TRUE AND TRUE)"
90 PRINT "-1 AND 0 ="; -1 AND 0; "(TRUE AND FALSE)"
100 PRINT "0 AND -1 ="; 0 AND -1; "(FALSE AND TRUE)"
110 PRINT "0 AND 0 ="; 0 AND 0; "(FALSE AND FALSE)"
120 PRINT
130 REM Test 2: OR operator
140 PRINT "Test 2: OR operator"
150 PRINT "-1 OR -1 ="; -1 OR -1; "(TRUE OR TRUE)"
160 PRINT "-1 OR 0 ="; -1 OR 0; "(TRUE OR FALSE)"
170 PRINT "0 OR -1 ="; 0 OR -1; "(FALSE OR TRUE)"
180 PRINT "0 OR 0 ="; 0 OR 0; "(FALSE OR FALSE)"
190 PRINT
200 REM Test 3: NOT operator
210 PRINT "Test 3: NOT operator"
220 PRINT "NOT -1 ="; NOT -1; "(NOT TRUE)"
230 PRINT "NOT 0 ="; NOT 0; "(NOT FALSE)"
240 PRINT "NOT 5 ="; NOT 5; "(bitwise complement)"
250 PRINT
260 REM Test 4: XOR operator
270 PRINT "Test 4: XOR operator"
280 PRINT "-1 XOR -1 ="; -1 XOR -1; "(TRUE XOR TRUE)"
290 PRINT "-1 XOR 0 ="; -1 XOR 0; "(TRUE XOR FALSE)"
300 PRINT "0 XOR -1 ="; 0 XOR -1; "(FALSE XOR TRUE)"
310 PRINT "0 XOR 0 ="; 0 XOR 0; "(FALSE XOR FALSE)"
320 PRINT
330 REM Test 5: Combined logical operations
340 PRINT "Test 5: Combined operations"
350 A = -1 : B = 0 : C = -1
360 PRINT "(A AND B) OR C ="; (A AND B) OR C
370 PRINT "A AND (B OR C) ="; A AND (B OR C)
380 PRINT "NOT (A AND B) ="; NOT (A AND B)
390 PRINT
400 REM Test 6: Bitwise operations with numbers
410 PRINT "Test 6: Bitwise operations"
420 PRINT "5 AND 3 ="; 5 AND 3; "(binary 101 AND 011)"
430 PRINT "5 OR 3 ="; 5 OR 3; "(binary 101 OR 011)"
440 PRINT "5 XOR 3 ="; 5 XOR 3; "(binary 101 XOR 011)"
450 PRINT
460 REM Test 7: Logical in conditionals
470 PRINT "Test 7: Logical operators in IF"
480 X = 10 : Y = 20
490 IF X > 5 AND Y < 30 THEN PRINT "Both conditions true"
500 IF X > 15 OR Y < 30 THEN PRINT "At least one true"
510 IF NOT (X > 15) THEN PRINT "X not > 15"
520 PRINT
530 PRINT "Logical operator tests complete!"
540 END
