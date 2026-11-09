10 REM Test OPTION BASE
20 REM Note: OPTION BASE must come before DIM statements
30 PRINT "Testing OPTION BASE"
40 PRINT "==================="
50 PRINT
60 REM Test 1: OPTION BASE 1 must come first
70 PRINT "Test 1: OPTION BASE 1"
80 OPTION BASE 1
90 DIM B(5)
100 B(1) = 100
110 B(2) = 200
120 B(5) = 500
130 PRINT "B(1) ="; B(1); "(first element)"
140 PRINT "B(2) ="; B(2)
150 PRINT "B(5) ="; B(5); "(last element)"
160 PRINT
170 REM Test 2: Multi-dimensional with BASE 1
180 PRINT "Test 2: Multi-dim array with BASE 1"
190 DIM C(3, 3)
200 C(1, 1) = 11
210 C(1, 3) = 13
220 C(3, 1) = 31
230 C(3, 3) = 33
240 PRINT "C(1,1) ="; C(1, 1)
250 PRINT "C(1,3) ="; C(1, 3)
260 PRINT "C(3,1) ="; C(3, 1)
270 PRINT "C(3,3) ="; C(3, 3)
280 PRINT
290 REM Test 3: Array size with BASE 1
300 PRINT "Test 3: Array sizes"
310 DIM D(10)
320 PRINT "DIM D(10) with BASE 1"
330 PRINT "Elements: D(1) through D(10)"
340 D(1) = 1
350 D(10) = 10
360 PRINT "D(1) ="; D(1); ", D(10) ="; D(10)
370 PRINT
380 REM Test 4: Loop through BASE 1 array
390 PRINT "Test 4: Loop with BASE 1"
400 DIM E(5)
410 FOR I = 1 TO 5
420 E(I) = I * 10
430 NEXT I
440 PRINT "Array E:";
450 FOR I = 1 TO 5
460 PRINT E(I);
470 NEXT I
480 PRINT
490 PRINT
500 PRINT "OPTION BASE tests complete!"
510 END
