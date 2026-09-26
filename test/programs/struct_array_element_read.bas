REM struct_array_element_read.bas -- struct-array element read by variable
REM index: circle{(I%)}.r% (what used to break examples/graphics/surks.bbc
REM past the ELLIPSE fix, fixed alongside it).
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 7
DIM circle{(4) x%, y%, r%, t%}
circle{(0)}.r% = 7
I% = 0
PRINT STR$(circle{(I%)}.r%)
