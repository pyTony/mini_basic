   10 REM Float accuracy facts (read-only pseudo-variables)
   20 PRINT "Decimal digits : "; _float_digits
   30 PRINT "Mantissa bits  : "; _float_mantissa
   40 PRINT "Radix          : "; _float_radix
   50 PRINT "IEEE 754       : "; _ieee754
   60 PRINT "Epsilon        : "; _epsilon
   70 PRINT
   80 REM NEAR - machine-relative close enough
   90 A = 1.0
  100 B = 1.0 + _epsilon / 2
  110 PRINT "NEAR(1, 1+eps/2) = "; NEAR(A, B)
  120 PRINT "NEAR(1, 1+2*eps) = "; NEAR(A, 1.0 + _epsilon * 2)
  130 PRINT
  140 REM NEAR with absolute tolerance
  150 PRINT "NEAR(0, 1E-10, 1E-9) = "; NEAR(0, 1E-10, 1E-9)
  160 PRINT
  170 REM NEARSIG - how many significant figures agree?
  180 PRINT "NEARSIG(pi, 3.14159, 6) = "; NEARSIG(3.14159265, 3.14159, 6)
  190 PRINT "NEARSIG(pi, 3.14159, 7) = "; NEARSIG(3.14159265, 3.14159, 7)