10 REM Test ERASE Statement
20 PRINT "Testing ERASE"
30 PRINT "============="
40 PRINT
50 REM Test 1: ERASE numeric array
60 PRINT "Test 1: ERASE numeric array"
70 DIM A(5)
80 FOR I = 0 TO 5
90 A(I) = I * 10
100 NEXT I
110 PRINT "Before ERASE: A(2) ="; A(2)
120 ERASE A
130 DIM A(5)
140 PRINT "After ERASE: A(2) ="; A(2); "(should be 0)"
150 PRINT
160 REM Test 2: ERASE string array
170 PRINT "Test 2: ERASE string array"
180 DIM B$(3)
190 B$(0) = "Hello"
200 B$(1) = "World"
210 B$(2) = "Test"
220 PRINT "Before ERASE: B$(1) = "; B$(1)
230 ERASE B$
240 DIM B$(3)
250 PRINT "After ERASE: B$(1) = '"; B$(1); "' (empty)"
260 PRINT "Length:"; LEN(B$(1))
270 PRINT
280 REM Test 3: ERASE multiple arrays
290 PRINT "Test 3: ERASE multiple arrays"
300 DIM C(3), D(3)
310 C(0) = 100 : C(1) = 200
320 D(0) = 300 : D(1) = 400
330 PRINT "Before: C(1) ="; C(1); "D(1) ="; D(1)
340 ERASE C, D
350 DIM C(3), D(3)
360 PRINT "After: C(1) ="; C(1); "D(1) ="; D(1)
370 PRINT
380 REM Test 4: Re-dimension after ERASE
390 PRINT "Test 4: Re-dimension after ERASE"
400 DIM E(10)
410 E(5) = 555
420 PRINT "Original DIM E(10), E(5) ="; E(5)
430 ERASE E
440 DIM E(20)
450 PRINT "After ERASE and DIM E(20), E(5) ="; E(5)
460 E(15) = 999
470 PRINT "E(15) ="; E(15); "(now accessible)"
480 PRINT
490 REM Test 5: Multi-dimensional array ERASE
500 PRINT "Test 5: Multi-dimensional array"
510 DIM F(3, 3)
520 F(1, 1) = 11
530 F(2, 2) = 22
540 PRINT "Before: F(1,1) ="; F(1, 1); "F(2,2) ="; F(2, 2)
550 ERASE F
560 DIM F(3, 3)
570 PRINT "After: F(1,1) ="; F(1, 1); "F(2,2) ="; F(2, 2)
580 PRINT
590 PRINT "ERASE tests complete!"
600 END
