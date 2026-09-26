REM struct_array_unwritten_index.bas -- DIM name{(n) members} allocates
REM indices 0..n inclusive; reading a member of an index that has never
REM been individually written must return the type default (0), not fail.
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 7 0
DIM circle{(4) x%, y%, r%, t%}
circle{(0)}.r% = 7
I% = 3
PRINT STR$(circle{(0)}.r%) + " " + STR$(circle{(I%)}.r%)
