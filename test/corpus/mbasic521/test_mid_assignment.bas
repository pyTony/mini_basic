10 REM Test MID$ Assignment (in-place string modification)
20 PRINT "Testing MID$ Assignment"
30 PRINT "======================="
40 PRINT
50 REM Test 1: Replace middle of string
60 PRINT "Test 1: Replace middle characters"
70 A$ = "HELLO WORLD"
80 PRINT "Original: "; A$
90 MID$(A$, 7, 5) = "BASIC"
100 PRINT "After MID$(A$, 7, 5) = "; CHR$(34); "BASIC"; CHR$(34); ":"
110 PRINT "Result: "; A$
120 PRINT
130 REM Test 2: Replace from start
140 PRINT "Test 2: Replace from start"
150 B$ = "12345678"
160 PRINT "Original: "; B$
170 MID$(B$, 1, 3) = "ABC"
180 PRINT "After MID$(B$, 1, 3) = "; CHR$(34); "ABC"; CHR$(34); ":"
190 PRINT "Result: "; B$
200 PRINT
210 REM Test 3: Replace at end
220 PRINT "Test 3: Replace near end"
230 C$ = "ABCDEFGH"
240 PRINT "Original: "; C$
250 MID$(C$, 6, 3) = "XYZ"
260 PRINT "After MID$(C$, 6, 3) = "; CHR$(34); "XYZ"; CHR$(34); ":"
270 PRINT "Result: "; C$
280 PRINT
290 REM Test 4: Replacement shorter than length
300 PRINT "Test 4: Short replacement"
310 D$ = "1234567890"
320 PRINT "Original: "; D$
330 MID$(D$, 3, 5) = "AB"
340 PRINT "After MID$(D$, 3, 5) = "; CHR$(34); "AB"; CHR$(34); " (2 chars):"
350 PRINT "Result: "; D$
360 PRINT
370 REM Test 5: Replacement longer than length (truncate)
380 PRINT "Test 5: Long replacement (truncated)"
390 E$ = "AAAAAAAAAA"
400 PRINT "Original: "; E$
410 MID$(E$, 3, 3) = "BCDEFGH"
420 PRINT "After MID$(E$, 3, 3) = "; CHR$(34); "BCDEFGH"; CHR$(34); ":"
430 PRINT "Result: "; E$
440 PRINT
450 REM Test 6: Single character replacement
460 PRINT "Test 6: Single character"
470 F$ = "TESTING"
480 PRINT "Original: "; F$
490 MID$(F$, 1, 1) = "B"
500 MID$(F$, 4, 1) = "K"
510 PRINT "After changing pos 1 and 4:"
520 PRINT "Result: "; F$
530 PRINT
540 PRINT "MID$ assignment tests complete!"
550 END
