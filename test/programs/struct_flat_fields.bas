REM struct_flat_fields.bas -- flat DIM name{a%,b$} read/write.
REM Plain BBC BASIC: also runs unmodified under BBCSDL / BB4W.
REM DIALECT: bbc
REM EXPECT: 4 4 P
DIM pt{ x%, y%, label$ }
pt.x% = 3 : pt.y% = 4 : pt.label$ = "P"
pt.x% = pt.x% + 1
PRINT STR$(pt.x%) + " " + STR$(pt.y%) + " " + pt.label$
