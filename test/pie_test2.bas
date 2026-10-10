COLOUR 15,&87,&CE,&FF
COLOUR 15+128
CLS

nSlices% = 3
DIM Label$(nSlices%-1), Value(nSlices%-1), Colour&(nSlices%-1)

Label$()  = "One", "Two", "Three"
Value()   = 3.45, 4.56, 5.67
Colour&() = 1, 2, 3

Value() *= 2 * PI / SUM(Value())

Cx% = @vdu%!208
Cy% = @vdu%!212
Rad = 300
Depth = 128

*REFRESH OFF
prev = 0
FOR Y% = Cy% TO Cy% + Depth STEP 2
  IF Y% = Cy% + Depth Colour&() OR= 8
  FOR I% = 0 TO nSlices%-1
    GCOL Colour&(I%)
    this = Value(I%)
    PROCsector(Cx%, Y%, Rad, prev, prev + this)
    prev += this
  NEXT
NEXT Y%
OSCLI "GSAVE """ + @tmp$ + "pie.tmp.bmp"" "+STR$(Cx%-Rad)+","+STR$(Cy%-Rad)+","+STR$(2*Rad)+","+STR$(2*Rad+Depth)
CLS
*REFRESH ON
OSCLI "DISPLAY """ + @tmp$ + "pie.tmp.bmp"" "+STR$(Cx%-Rad)+","+STR$(Cy%-Rad/2)+","+STR$(2*Rad)+","+STR$(Rad+Depth/2)

REPEAT WAIT 4 : UNTIL FALSE
END

DEF PROCsector(cx, cy, r, a, b)
MOVE cx+0.5, cy+0.5
MOVE cx+r*COSa+0.5,cy+r*SINa+0.5
PLOT 181,cx+r*COSb+0.5,cy+r*SINb+0.5
ENDPROC