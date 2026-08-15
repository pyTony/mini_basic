     0 A = 1: F = 1: F% = 1
    15 F = F * A: F% = F%* A
    20 PRINT A,"factorial = ";
    30 PRINT F, F%
    40 A = A + 1
    50 INPUT "NEXT? ", Y$
    60 IF Y$ <>"N" 15
