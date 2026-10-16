    10 SIZE = 8192: TIME = 0
    20 DIM FLAGS(8192)
    30 PRINT "Starting 10 iterations of the Sieve..."
    40 FOR I = 1 TO 10
    50   COUNT = 0
    60   FOR J = 1 TO SIZE: FLAGS(J) = 1: NEXT J
    70   FOR J = 1 TO SIZE
    80     IF FLAGS(J) = 0 THEN GOTO 140
    90       PRIME = J + J + 3
   100      K = J + PRIME
   110      IF K > SIZE THEN GOTO 130
   120        FLAGS(K) = 0: K = K + PRIME: GOTO 110
   130      COUNT = COUNT + 1
   140  NEXT J
   150 NEXT I
   155 t = TIME / 100
   160 PRINT "Done. Primes found: "; COUNT;" TIME "; t
   170 REM INPUT "DONE",DUMMY$
