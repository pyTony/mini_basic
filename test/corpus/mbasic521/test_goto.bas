10 REM Test GOTO Statement
20 PRINT "Testing GOTO"
30 PRINT "============"
40 PRINT
50 REM Test 1: Simple forward GOTO
60 PRINT "Test 1: Forward GOTO"
70 GOTO 100
80 PRINT "  FAIL: Should not print this"
90 GOTO 110
100 PRINT "  PASS: Forward GOTO works"
110 PRINT
120 REM Test 2: Backward GOTO (with counter to prevent infinite loop)
130 PRINT "Test 2: Backward GOTO"
140 COUNT = 0
150 COUNT = COUNT + 1
160 IF COUNT = 3 THEN GOTO 180
170 GOTO 150
180 PRINT "  PASS: Backward GOTO works (looped"; COUNT; "times)"
190 PRINT
200 REM Test 3: GOTO with calculation
210 PRINT "Test 3: Conditional GOTO"
220 X = 10
230 IF X > 5 THEN GOTO 260
240 PRINT "  FAIL: Should have skipped this"
250 GOTO 270
260 PRINT "  PASS: Conditional GOTO works"
270 PRINT
280 REM Test 4: Multiple GOTOs
290 PRINT "Test 4: Multiple GOTO sequence"
300 GOTO 340
310 PRINT "  Step 2"
320 GOTO 360
330 END
340 PRINT "  Step 1"
350 GOTO 310
360 PRINT "  Step 3"
370 PRINT
380 PRINT "All GOTO tests complete!"
390 END
