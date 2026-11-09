10 REM Test String Functions
20 PRINT "Testing String Functions"
30 PRINT "========================"
40 PRINT
50 REM Test 1: LEFT$
60 PRINT "Test 1: LEFT$"
70 A$ = "HELLO WORLD"
80 PRINT "  LEFT$('HELLO WORLD', 5) ="; LEFT$(A$, 5)
90 IF LEFT$(A$, 5) = "HELLO" THEN PRINT "  PASS: LEFT$ works"
100 PRINT
110 REM Test 2: RIGHT$
120 PRINT "Test 2: RIGHT$"
130 PRINT "  RIGHT$('HELLO WORLD', 5) ="; RIGHT$(A$, 5)
140 IF RIGHT$(A$, 5) = "WORLD" THEN PRINT "  PASS: RIGHT$ works"
150 PRINT
160 REM Test 3: MID$
170 PRINT "Test 3: MID$"
180 PRINT "  MID$('HELLO WORLD', 7, 5) ="; MID$(A$, 7, 5)
190 IF MID$(A$, 7, 5) = "WORLD" THEN PRINT "  PASS: MID$ works"
200 PRINT
210 REM Test 4: LEN
220 PRINT "Test 4: LEN"
230 PRINT "  LEN('HELLO WORLD') ="; LEN(A$)
240 IF LEN(A$) = 11 THEN PRINT "  PASS: LEN works"
250 PRINT
260 REM Test 5: ASC and CHR$
270 PRINT "Test 5: ASC and CHR$"
280 PRINT "  ASC('A') ="; ASC("A")
290 PRINT "  CHR$(65) ="; CHR$(65)
300 IF ASC("A") = 65 AND CHR$(65) = "A" THEN PRINT "  PASS: ASC and CHR$ work"
310 PRINT
320 REM Test 6: STR$ and VAL
330 PRINT "Test 6: STR$ and VAL"
340 N = 123
350 S$ = STR$(N)
360 PRINT "  STR$(123) ="; S$
370 PRINT "  VAL('123') ="; VAL("123")
380 IF VAL(S$) = 123 THEN PRINT "  PASS: STR$ and VAL work"
390 PRINT
400 REM Test 7: String concatenation
410 PRINT "Test 7: String concatenation (+)"
420 B$ = "HELLO"
430 C$ = "WORLD"
440 D$ = B$ + " " + C$
450 PRINT "  'HELLO' + ' ' + 'WORLD' ="; D$
460 IF D$ = "HELLO WORLD" THEN PRINT "  PASS: String concatenation works"
470 PRINT
480 REM Test 8: INSTR
490 PRINT "Test 8: INSTR"
500 E$ = "ABCDEFGH"
510 PRINT "  INSTR('ABCDEFGH', 'DEF') ="; INSTR(E$, "DEF")
520 IF INSTR(E$, "DEF") = 4 THEN PRINT "  PASS: INSTR works"
530 PRINT
540 REM Test 9: SPACE$
550 PRINT "Test 9: SPACE$"
560 F$ = "A" + SPACE$(5) + "B"
570 PRINT "  'A' + SPACE$(5) + 'B' ="; F$
580 IF LEN(F$) = 7 THEN PRINT "  PASS: SPACE$ works"
590 PRINT
600 REM Test 10: STRING$
610 PRINT "Test 10: STRING$"
620 G$ = STRING$(5, 42)
630 PRINT "  STRING$(5, 42) ="; G$; "(5 asterisks)"
640 IF LEN(G$) = 5 THEN PRINT "  PASS: STRING$ works"
650 PRINT
660 PRINT "All string function tests complete!"
670 END
