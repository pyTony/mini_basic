    10 REM Store a binary value
    20 my_byte% = %11001010
    30 REM Mask the lower 4 bits
    40 result% = my_byte%AND%00001111
    50 PRINT STR$~(result%)
