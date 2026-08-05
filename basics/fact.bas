    10       PRINT FNfact(100)
    20       END
    30       DEF FNfact(n%)
    40       IF n% < 2 THEN
    50         = 1
    60       ELSE
    70         = FNfact(n%-1) * n%
    80       ENDIF
    90       END DEF
