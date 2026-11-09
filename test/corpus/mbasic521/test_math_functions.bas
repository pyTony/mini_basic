10 REM Test Math Functions
20 PRINT "Testing Math Functions"
30 PRINT "======================"
40 PRINT
50 REM Test 1: ABS (absolute value)
60 PRINT "Test 1: ABS"
70 PRINT "  ABS(-10) ="; ABS(-10)
80 PRINT "  ABS(10) ="; ABS(10)
90 IF ABS(-10) = 10 AND ABS(10) = 10 THEN PRINT "  PASS: ABS works"
100 PRINT
110 REM Test 2: SGN (sign)
120 PRINT "Test 2: SGN"
130 PRINT "  SGN(-5) ="; SGN(-5)
140 PRINT "  SGN(0) ="; SGN(0)
150 PRINT "  SGN(5) ="; SGN(5)
160 IF SGN(-5) = -1 AND SGN(0) = 0 AND SGN(5) = 1 THEN PRINT "  PASS: SGN works"
170 PRINT
180 REM Test 3: INT (integer part)
190 PRINT "Test 3: INT"
200 PRINT "  INT(10.9) ="; INT(10.9)
210 PRINT "  INT(-10.9) ="; INT(-10.9)
220 IF INT(10.9) = 10 AND INT(-10.9) = -11 THEN PRINT "  PASS: INT works"
230 PRINT
240 REM Test 4: FIX (truncate)
250 PRINT "Test 4: FIX"
260 PRINT "  FIX(10.9) ="; FIX(10.9)
270 PRINT "  FIX(-10.9) ="; FIX(-10.9)
280 IF FIX(10.9) = 10 AND FIX(-10.9) = -10 THEN PRINT "  PASS: FIX works"
290 PRINT
300 REM Test 5: SQR (square root)
310 PRINT "Test 5: SQR"
320 PRINT "  SQR(16) ="; SQR(16)
330 PRINT "  SQR(25) ="; SQR(25)
340 IF SQR(16) = 4 AND SQR(25) = 5 THEN PRINT "  PASS: SQR works"
350 PRINT
360 REM Test 6: Exponentiation
370 PRINT "Test 6: Exponentiation (^)"
380 PRINT "  2 ^ 3 ="; 2 ^ 3
390 PRINT "  5 ^ 2 ="; 5 ^ 2
400 IF 2 ^ 3 = 8 AND 5 ^ 2 = 25 THEN PRINT "  PASS: ^ works"
410 PRINT
420 REM Test 7: SIN/COS/TAN (basic test)
430 PRINT "Test 7: Trigonometric functions"
440 PI = 3.14159265
450 PRINT "  SIN(0) ="; SIN(0)
460 PRINT "  COS(0) ="; COS(0)
470 PRINT "  TAN(0) ="; TAN(0)
480 REM Just test they don't error - exact values depend on precision
490 IF SIN(0) = 0 AND COS(0) = 1 AND TAN(0) = 0 THEN PRINT "  PASS: Trig functions work"
500 PRINT
510 REM Test 8: EXP and LOG
520 PRINT "Test 8: EXP and LOG"
530 PRINT "  EXP(0) ="; EXP(0)
540 PRINT "  LOG(1) ="; LOG(1)
550 IF EXP(0) = 1 AND LOG(1) = 0 THEN PRINT "  PASS: EXP and LOG work"
560 PRINT
570 REM Test 9: ATN (arctangent)
580 PRINT "Test 9: ATN"
590 PRINT "  ATN(0) ="; ATN(0)
600 IF ATN(0) = 0 THEN PRINT "  PASS: ATN works"
610 PRINT
620 REM Test 10: CINT (convert to integer with rounding)
630 PRINT "Test 10: CINT"
640 PRINT "  CINT(10.4) ="; CINT(10.4)
650 PRINT "  CINT(10.6) ="; CINT(10.6)
660 IF CINT(10.4) = 10 AND CINT(10.6) = 11 THEN PRINT "  PASS: CINT works"
670 PRINT
680 PRINT "All math function tests complete!"
690 END
