REM struct_array_element_write.bas -- DIM name{(n) a%,b%} element write.
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: ok
DIM circle{(4) x%, y%, r%, t%}
circle{(0)}.x% = 5
circle{(0)}.r% = 7
PRINT "ok"
