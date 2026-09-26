    10   DEF FNfact(n%)
    20     IF n% < 2 THEN
    30          = 1
    40     ELSE
    50          = FNfact(n%-1) * n%
    60     ENDIF
    70  END DEF
