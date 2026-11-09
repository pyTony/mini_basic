10 REM Test FOR/NEXT Loops
20 REM Tests basic loops, STEP, nested loops, negative steps
30 PRINT "Testing FOR/NEXT Loops"
40 PRINT "======================"
50 PRINT
60 REM Test 1: Basic FOR loop
70 PRINT "Test 1: Basic FOR loop (1 TO 5)"
80 FOR I = 1 TO 5
90 PRINT I;
100 NEXT I
110 PRINT
120 PRINT
130 REM Test 2: FOR loop with STEP
140 PRINT "Test 2: FOR loop with STEP 2 (0 TO 10 STEP 2)"
150 FOR I = 0 TO 10 STEP 2
160 PRINT I;
170 NEXT I
180 PRINT
190 PRINT
200 REM Test 3: Negative STEP
210 PRINT "Test 3: Negative STEP (10 TO 1 STEP -2)"
220 FOR I = 10 TO 1 STEP -2
230 PRINT I;
240 NEXT I
250 PRINT
260 PRINT
270 REM Test 4: STEP with decimal
280 PRINT "Test 4: STEP with decimal (0 TO 2 STEP 0.5)"
290 FOR I = 0 TO 2 STEP 0.5
300 PRINT I;
310 NEXT I
320 PRINT
330 PRINT
340 REM Test 5: Nested loops
350 PRINT "Test 5: Nested loops (2x3 grid)"
360 FOR I = 1 TO 2
370 FOR J = 1 TO 3
380 PRINT "(" + STR$(I) + "," + STR$(J) + ")";
390 NEXT J
400 PRINT
410 NEXT I
420 PRINT
430 REM Test 6: Loop variable after loop
440 PRINT "Test 6: Loop variable value after loop"
450 FOR I = 1 TO 5
460 NEXT I
470 PRINT "I after loop ="; I; "(should be 6)"
480 PRINT
490 REM Test 7: Single iteration
500 PRINT "Test 7: Single iteration (5 TO 5)"
510 FOR I = 5 TO 5
520 PRINT "I ="; I
530 NEXT I
540 PRINT
550 REM Test 8: No iterations (start > end with positive step)
560 PRINT "Test 8: No iterations (10 TO 1)"
570 C = 0
580 FOR I = 10 TO 1
590 C = C + 1
600 NEXT I
610 PRINT "Iterations:"; C; "(should be 0)"
620 PRINT
630 REM Test 9: Accumulator in loop
640 PRINT "Test 9: Sum 1 to 10"
650 S = 0
660 FOR I = 1 TO 10
670 S = S + I
680 NEXT I
690 PRINT "Sum ="; S; "(should be 55)"
700 PRINT
710 REM Test 10: Triple nested loops
720 PRINT "Test 10: Triple nested (2x2x2)"
730 FOR I = 1 TO 2
740 FOR J = 1 TO 2
750 FOR K = 1 TO 2
760 PRINT I; J; K;
770 NEXT K
780 NEXT J
790 NEXT I
800 PRINT
810 PRINT
820 PRINT "FOR/NEXT tests complete!"
830 END
