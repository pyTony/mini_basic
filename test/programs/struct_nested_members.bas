REM struct_nested_members.bas -- nested sub-structures inside a struct
REM array, a byte (&) member, and compound assignment on members (the
REM patterns examples/graphics/bounce.bbc uses).
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 7.5 44 0
REM EXPECT: 3 hi
DIM Ball{(3) Pos{x,y}, Vel{h,v}, Colour&, Rad%}
DIM P{a, Q{b%, R{c$}}}
I% = 1
Ball{(I%)}.Pos.x = 5
Ball{(I%)}.Vel.h = 2.5
Ball{(1)}.Colour& = 300
Ball{(I%)}.Pos.x += Ball{(I%)}.Vel.h
PRINT STR$(Ball{(1)}.Pos.x);" ";STR$(Ball{(1)}.Colour&);" ";STR$(Ball{(2)}.Pos.y)
P.Q.b% = 1 : P.Q.b% += 2 : P.Q.R.c$ = "hi"
PRINT STR$(P.Q.b%);" ";P.Q.R.c$
