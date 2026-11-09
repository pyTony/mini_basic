10 REM Test DEF FN User-Defined Functions
20 REM Tests single-line functions with parameters
30 PRINT "Testing DEF FN (User-Defined Functions)"
40 PRINT "========================================"
50 PRINT
60 REM Test 1: Simple function with one parameter
70 DEF FN SQUARE(X) = X * X
80 PRINT "Test 1: FN SQUARE(5) ="; FN SQUARE(5); "(expected: 25)"
90 PRINT "        FN SQUARE(10) ="; FN SQUARE(10); "(expected: 100)"
100 PRINT
110 REM Test 2: Function with two parameters
120 DEF FN ADD(A, B) = A + B
130 PRINT "Test 2: FN ADD(3, 7) ="; FN ADD(3, 7); "(expected: 10)"
140 PRINT "        FN ADD(100, 50) ="; FN ADD(100, 50); "(expected: 150)"
150 PRINT
160 REM Test 3: Function with expressions
170 DEF FN CIRCLE(R) = 3.14159 * R * R
180 PRINT "Test 3: FN CIRCLE(5) ="; FN CIRCLE(5); "(area of circle r=5)"
190 PRINT "        FN CIRCLE(10) ="; FN CIRCLE(10); "(area of circle r=10)"
200 PRINT
210 REM Test 4: Function calling another function
220 DEF FN DOUBLE(X) = X * 2
230 DEF FN QUAD(X) = FN DOUBLE(FN DOUBLE(X))
240 PRINT "Test 4: FN QUAD(5) ="; FN QUAD(5); "(expected: 20)"
250 PRINT
260 REM Test 5: String function
270 DEF FN GREET$(N$) = "Hello, " + N$ + "!"
280 PRINT "Test 5: FN GREET$("; CHR$(34); "World"; CHR$(34); ") ="
290 PRINT "        "; FN GREET$("World")
300 PRINT
310 REM Test 6: Function with integer parameters
320 DEF FN MAX%(A%, B%) = -((A% > B%) * A% + (B% >= A%) * B%)
330 PRINT "Test 6: FN MAX%(10, 20) ="; FN MAX%(10, 20); "(expected: 20)"
340 PRINT "        FN MAX%(50, 30) ="; FN MAX%(50, 30); "(expected: 50)"
350 PRINT
360 REM Test 7: Trigonometric function
370 DEF FN DEGREES(R) = R * 57.2958
380 PRINT "Test 7: FN DEGREES(1.5708) ="; FN DEGREES(1.5708); "(~90 degrees)"
390 PRINT
400 REM Test 8: Function in expression
410 DEF FN CUBE(X) = X * X * X
420 Y = 10 + FN CUBE(3)
430 PRINT "Test 8: 10 + FN CUBE(3) ="; Y; "(expected: 37)"
440 PRINT
450 REM Test 9: Function with division
460 DEF FN AVG(A, B) = (A + B) / 2
470 PRINT "Test 9: FN AVG(10, 20) ="; FN AVG(10, 20); "(expected: 15)"
480 PRINT "        FN AVG(5, 15) ="; FN AVG(5, 15); "(expected: 10)"
490 PRINT
500 REM Test 10: Multiple function definitions
510 DEF FN F1(X) = X + 1
520 DEF FN F2(X) = X + 2
530 DEF FN F3(X) = X + 3
540 PRINT "Test 10: FN F1(10) ="; FN F1(10); ", FN F2(10) ="; FN F2(10); ", FN F3(10) ="; FN F3(10)
550 PRINT
560 PRINT "DEF FN tests complete!"
570 END
