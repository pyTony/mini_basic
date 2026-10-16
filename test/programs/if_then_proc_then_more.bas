REM if_then_proc_then_more.bas -- IF ... THEN PROCname : more statements.
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 1 0
REM EXPECT: 0 5
N% = 0 : C% = 5
IF C% > 2 THEN PROC_add : C% = 0
PRINT STR$(N%);" ";STR$(C%)
N% = 0 : C% = 5
IF C% > 9 THEN PROC_add : C% = 0
PRINT STR$(N%);" ";STR$(C%)
END
DEF PROC_add
N% += 1
ENDPROC
