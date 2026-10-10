MODE 8
GCOL 1
Cx% = @vdu%!208
Cy% = @vdu%!212
Rad = 300
Depth = 128

count% = 0
FOR Y% = Cy% TO Cy% + Depth STEP 2
  count% += 1
NEXT Y%
PRINT "Iterations = "; count%

GCOL 1
PROCsector(Cx%, Cy%, Rad, 0, 1.5845)

REPEAT WAIT 2 : UNTIL FALSE
END

DEF PROCsector(cx, cy, r, a, b)
MOVE cx+0.5, cy+0.5
MOVE cx+r*COSa+0.5, cy+r*SINa+0.5
PLOT 181, cx+r*COSb+0.5, cy+r*SINb+0.5
ENDPROC