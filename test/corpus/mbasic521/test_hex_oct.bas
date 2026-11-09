10 REM Test HEX$ and OCT$ Functions
20 PRINT "Testing HEX$ and OCT$"
30 PRINT "====================="
40 PRINT
50 REM Test 1: HEX$ with decimal numbers
60 PRINT "Test 1: HEX$ conversion"
70 PRINT "HEX$(10) ="; HEX$(10); "(expected: A)"
80 PRINT "HEX$(15) ="; HEX$(15); "(expected: F)"
90 PRINT "HEX$(16) ="; HEX$(16); "(expected: 10)"
100 PRINT "HEX$(255) ="; HEX$(255); "(expected: FF)"
110 PRINT "HEX$(256) ="; HEX$(256); "(expected: 100)"
120 PRINT
130 REM Test 2: OCT$ with decimal numbers
140 PRINT "Test 2: OCT$ conversion"
150 PRINT "OCT$(8) ="; OCT$(8); "(expected: 10)"
160 PRINT "OCT$(10) ="; OCT$(10); "(expected: 12)"
170 PRINT "OCT$(64) ="; OCT$(64); "(expected: 100)"
180 PRINT "OCT$(255) ="; OCT$(255); "(expected: 377)"
190 PRINT
200 REM Test 3: HEX$ with larger numbers
210 PRINT "Test 3: HEX$ with larger numbers"
220 PRINT "HEX$(1000) ="; HEX$(1000)
230 PRINT "HEX$(4095) ="; HEX$(4095); "(expected: FFF)"
240 PRINT "HEX$(65535) ="; HEX$(65535); "(expected: FFFF)"
250 PRINT
260 REM Test 4: OCT$ with larger numbers
270 PRINT "Test 4: OCT$ with larger numbers"
280 PRINT "OCT$(100) ="; OCT$(100)
290 PRINT "OCT$(511) ="; OCT$(511); "(expected: 777)"
300 PRINT "OCT$(512) ="; OCT$(512); "(expected: 1000)"
310 PRINT
320 REM Test 5: HEX$ with 0 and powers of 2
330 PRINT "Test 5: HEX$ with special values"
340 PRINT "HEX$(0) ="; HEX$(0); "(expected: 0)"
350 PRINT "HEX$(1) ="; HEX$(1); "(expected: 1)"
360 PRINT "HEX$(128) ="; HEX$(128); "(expected: 80)"
370 PRINT "HEX$(1024) ="; HEX$(1024); "(expected: 400)"
380 PRINT
390 REM Test 6: OCT$ with 0 and powers of 8
400 PRINT "Test 6: OCT$ with special values"
410 PRINT "OCT$(0) ="; OCT$(0); "(expected: 0)"
420 PRINT "OCT$(1) ="; OCT$(1); "(expected: 1)"
430 PRINT "OCT$(7) ="; OCT$(7); "(expected: 7)"
440 PRINT "OCT$(9) ="; OCT$(9); "(expected: 11)"
450 PRINT
460 REM Test 7: Use in expressions
470 PRINT "Test 7: HEX$/OCT$ in expressions"
480 H$ = "Value in hex: " + HEX$(42)
490 O$ = "Value in oct: " + OCT$(42)
500 PRINT H$
510 PRINT O$
520 PRINT
530 REM Test 8: Common hex values
540 PRINT "Test 8: Common hex values"
550 FOR I = 0 TO 15
560 PRINT HEX$(I);
570 IF I < 15 THEN PRINT ",";
580 NEXT I
590 PRINT
600 PRINT
610 PRINT "HEX$ and OCT$ tests complete!"
620 END
