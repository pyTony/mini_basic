10 REM Test TAB and SPC Functions
20 PRINT "Testing TAB and SPC"
30 PRINT "==================="
40 PRINT
50 REM Test 1: TAB to specific column
60 PRINT "Test 1: TAB function"
70 PRINT "A"; TAB(10); "B"; TAB(20); "C"
80 PRINT "1"; TAB(10); "2"; TAB(20); "3"
90 PRINT
100 REM Test 2: SPC for spaces
110 PRINT "Test 2: SPC function"
120 PRINT "A"; SPC(5); "B"; SPC(5); "C"
130 PRINT "X"; SPC(10); "Y"
140 PRINT
150 REM Test 3: TAB with different columns
160 PRINT "Test 3: Multiple TAB positions"
170 PRINT TAB(5); "*"; TAB(15); "*"; TAB(25); "*"
180 PRINT TAB(10); "Centered"
190 PRINT
200 REM Test 4: SPC with different counts
210 PRINT "Test 4: Various SPC counts"
220 PRINT "Gap1"; SPC(1); "Gap2"; SPC(2); "Gap3"; SPC(3); "End"
230 PRINT
240 REM Test 5: TAB in loops
250 PRINT "Test 5: TAB in FOR loop"
260 FOR I = 1 TO 3
270 PRINT TAB(I * 5); I
280 NEXT I
290 PRINT
300 REM Test 6: Combined TAB and SPC
310 PRINT "Test 6: TAB and SPC together"
320 PRINT TAB(5); "Start"; SPC(3); "Middle"; SPC(3); "End"
330 PRINT
340 REM Test 7: TAB with expressions
350 PRINT "Test 7: TAB with expressions"
360 C = 15
370 PRINT TAB(C); "At column 15"
380 PRINT TAB(C + 5); "At column 20"
390 PRINT
400 REM Test 8: SPC with expressions
410 PRINT "Test 8: SPC with expressions"
420 N = 4
430 PRINT "A"; SPC(N); "B"; SPC(N * 2); "C"
440 PRINT
450 PRINT "TAB/SPC tests complete!"
460 END
