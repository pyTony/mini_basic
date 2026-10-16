REM struct_array_cross_var_index.bas -- struct-array element written via one
REM index variable, read back via a different variable holding the same
REM value. This is the exact pattern that broke examples/graphics/surks.bbc
REM (a circle collision-check loop writes with one loop variable and reads
REM back with another).
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 7
DIM circle{(4) x%, y%, r%, t%}
N% = 0
circle{(N%)}.r% = 7
I% = 0
PRINT STR$(circle{(I%)}.r%)
