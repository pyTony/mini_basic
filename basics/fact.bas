  PRINT FNfact(100)
  END
  DEF FNfact(n%)
    IF n% < 2 THEN
         = 1
    ELSE
         = FNfact(n%-1) * n%
    ENDIF
 END DEF
