REM struct_whole_element_copy.bas -- copy a whole struct-array element
REM (including nested members) with Ball{(i%)} = Ball{(i%+1)}, and a whole
REM struct with a{} = b{}.
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 9 4 two
REM EXPECT: 0 0
REM EXPECT: 3.5 2
DIM Ball{(3) Pos{x,y}, Colour&, N$}
DIM A{p, q%}, B{p, q%}
Ball{(2)}.Pos.x = 9 : Ball{(2)}.Colour& = 4 : Ball{(2)}.N$ = "two"
i% = 1
Ball{(i%)} = Ball{(i%+1)}
PRINT STR$(Ball{(1)}.Pos.x);" ";STR$(Ball{(1)}.Colour&);" ";Ball{(1)}.N$
Ball{(i%)} = Ball{(0)}
PRINT STR$(Ball{(1)}.Pos.x);" ";STR$(Ball{(1)}.Colour&)
B.p = 3.5 : B.q% = 2
A{} = B{}
PRINT STR$(A.p);" ";STR$(A.q%)
