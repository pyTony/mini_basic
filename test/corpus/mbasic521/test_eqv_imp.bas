10 REM Test EQV and IMP operators
20 REM Based on MBASIC 5.21 truth tables
30 PRINT "Testing EQV (equivalence) operator:"
40 PRINT "-1 EQV -1 = "; -1 EQV -1; " (expected: -1)"
50 PRINT "-1 EQV 0 = "; -1 EQV 0; " (expected: 0)"
60 PRINT "0 EQV -1 = "; 0 EQV -1; " (expected: 0)"
70 PRINT "0 EQV 0 = "; 0 EQV 0; " (expected: -1)"
80 PRINT
90 PRINT "Testing IMP (implication) operator:"
100 PRINT "-1 IMP -1 = "; -1 IMP -1; " (expected: -1)"
110 PRINT "-1 IMP 0 = "; -1 IMP 0; " (expected: 0)"
120 PRINT "0 IMP -1 = "; 0 IMP -1; " (expected: -1)"
130 PRINT "0 IMP 0 = "; 0 IMP 0; " (expected: -1)"
140 PRINT
150 REM Test with non-boolean integer values (bitwise operations)
160 PRINT "Bitwise tests:"
170 PRINT "5 EQV 3 = "; 5 EQV 3; " (5=101b, 3=011b)"
180 PRINT "5 IMP 3 = "; 5 IMP 3; " (5=101b, 3=011b)"
190 PRINT "15 EQV 7 = "; 15 EQV 7; " (15=1111b, 7=0111b)"
200 PRINT "15 IMP 7 = "; 15 IMP 7; " (15=1111b, 7=0111b)"
210 END
