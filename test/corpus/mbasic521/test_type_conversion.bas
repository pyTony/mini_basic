10 REM Test Type Conversion Functions
20 PRINT "Testing Type Conversion"
30 PRINT "======================="
40 PRINT
50 REM Test 1: CINT - Convert to integer
60 PRINT "Test 1: CINT (convert to integer)"
70 PRINT "CINT(3.2) ="; CINT(3.2); "(expected: 3)"
80 PRINT "CINT(3.7) ="; CINT(3.7); "(expected: 4)"
90 PRINT "CINT(-2.3) ="; CINT(-2.3); "(expected: -2)"
100 PRINT "CINT(-2.7) ="; CINT(-2.7); "(expected: -3)"
110 PRINT
120 REM Test 2: CSNG - Convert to single precision
130 PRINT "Test 2: CSNG (convert to single)"
140 A# = 123.456789012345
150 B! = CSNG(A#)
160 PRINT "Double:"; A#
170 PRINT "Single:"; B!
180 PRINT
190 REM Test 3: CDBL - Convert to double precision
200 PRINT "Test 3: CDBL (convert to double)"
210 C! = 3.14
220 D# = CDBL(C!)
230 PRINT "Single:"; C!
240 PRINT "Double:"; D#
250 PRINT
260 REM Test 4: STR$ and VAL conversions
270 PRINT "Test 4: STR$ and VAL"
280 N = 42
290 S$ = STR$(N)
300 PRINT "Number to string: STR$(42) ="; S$
310 V = VAL(S$)
320 PRINT "String to number: VAL("; S$; ") ="; V
330 PRINT
340 REM Test 5: CINT with type suffixes
350 PRINT "Test 5: CINT vs % suffix"
360 X! = 10.7
370 Y% = X!
380 Z% = CINT(X!)
390 PRINT "X! = 10.7"
400 PRINT "Y% = X! gives"; Y%
410 PRINT "CINT(X!) gives"; Z%
420 PRINT
430 REM Test 6: Implicit conversions
440 PRINT "Test 6: Implicit type conversion"
450 I% = 5
460 F! = 2.5
470 R = I% + F!
480 PRINT "Integer 5 + Single 2.5 ="; R
490 PRINT
500 REM Test 7: String to numeric with VAL
510 PRINT "Test 7: VAL with various strings"
520 PRINT "VAL("; CHR$(34); "123"; CHR$(34); ") ="; VAL("123")
530 PRINT "VAL("; CHR$(34); "3.14"; CHR$(34); ") ="; VAL("3.14")
540 PRINT "VAL("; CHR$(34); "-42"; CHR$(34); ") ="; VAL("-42")
550 PRINT "VAL("; CHR$(34); "12.5E2"; CHR$(34); ") ="; VAL("12.5E2")
560 PRINT
570 REM Test 8: Numeric to string with STR$
580 PRINT "Test 8: STR$ with various numbers"
590 PRINT "STR$(100) ="; STR$(100)
600 PRINT "STR$(-50) ="; STR$(-50)
610 PRINT "STR$(3.14159) ="; STR$(3.14159)
620 PRINT
630 REM Test 9: ASC and CHR$ for character conversion
640 PRINT "Test 9: ASC and CHR$ conversion"
650 PRINT "ASC("; CHR$(34); "A"; CHR$(34); ") ="; ASC("A")
660 PRINT "CHR$(65) ="; CHR$(65)
670 PRINT "ASC("; CHR$(34); "0"; CHR$(34); ") ="; ASC("0")
680 PRINT "CHR$(48) ="; CHR$(48)
690 PRINT
700 REM Test 10: Conversion with expressions
710 PRINT "Test 10: Conversions in expressions"
720 A = CINT(10.6) + CINT(20.4)
730 PRINT "CINT(10.6) + CINT(20.4) ="; A
740 B$ = STR$(CINT(3.7))
750 PRINT "STR$(CINT(3.7)) ="; B$
760 PRINT
770 PRINT "Type conversion tests complete!"
780 END
