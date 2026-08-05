    10 DEF FNbin(I%)
    20     IF I% = 0 THEN
    30     = "0"
    40     ELSE
    50     = FNbin_(I%)
    60     END IF
    70 END DEF
    80 DEF FNbin_(I%)
    90     IF I%>0 THEN
   100         = FNbin_(I% DIV 2) + STR$(I% MOD 2)
   110     ELSE
   120         = ""
   130     END IF
   140 END DEF
