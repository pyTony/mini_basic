10 REM Test PRINT USING Formatted Output
20 PRINT "Testing PRINT USING"
30 PRINT "==================="
40 PRINT
50 REM Test 1: Number formatting with #
60 PRINT "Test 1: Basic number formatting"
70 PRINT USING "###"; 42
80 PRINT USING "#####"; 12345
90 PRINT
100 REM Test 2: Decimal places with .##
110 PRINT "Test 2: Decimal formatting"
120 PRINT USING "##.##"; 3.14
130 PRINT USING "###.##"; 123.456
140 PRINT
150 REM Test 3: Leading dollar sign
160 PRINT "Test 3: Currency formatting"
170 PRINT USING "$###.##"; 99.95
180 PRINT USING "$####.##"; 1234.56
190 PRINT
200 REM Test 4: Comma separator
210 PRINT "Test 4: Comma separators"
220 PRINT USING "#,###"; 1234
230 PRINT USING "##,###.##"; 12345.67
240 PRINT
250 REM Test 5: Plus/minus signs
260 PRINT "Test 5: Sign formatting"
270 PRINT USING "+###"; 42
280 PRINT USING "+###"; -42
290 PRINT
300 REM Test 6: String formatting with !
310 PRINT "Test 6: String first character (!)"
320 PRINT USING "!"; "HELLO"
330 PRINT USING "Name: !"; "World"
340 PRINT
350 REM Test 7: Fixed-width strings with \  \
360 PRINT "Test 7: Fixed-width strings"
370 PRINT USING "\    \"; "HELLO"
380 PRINT USING "\  \"; "TEST"
390 PRINT
400 REM Test 8: Multiple values
410 PRINT "Test 8: Multiple values"
420 PRINT USING "### ### ###"; 10; 20; 30
430 PRINT USING "Name: \      \ Age: ##"; "Alice"; 25
440 PRINT
450 REM Test 9: Exponential format
460 PRINT "Test 9: Exponential notation"
470 PRINT USING "##.##^^^^"; 12345.6
480 PRINT USING "##.##^^^^"; 0.00123
490 PRINT
500 REM Test 10: Overflow with asterisks
510 PRINT "Test 10: Overflow handling"
520 PRINT USING "###"; 12345
530 PRINT USING "##.##"; 123.456
540 PRINT
550 PRINT "PRINT USING tests complete!"
560 END
