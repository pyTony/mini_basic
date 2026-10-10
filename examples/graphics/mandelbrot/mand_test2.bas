10 W = 80
20 H = 25
30 DIM palette(255,2)
40 FOR c = 0 TO 254
50     palette(c,0) = INT(127.5 * (1 + SIN(c * 0.1)))
60     palette(c,1) = INT(127.5 * (1 + SIN(c * 0.15)))
70     palette(c,2) = INT(127.5 * (1 + SIN(c * 0.2)))
80 NEXT c
90 FOR Y = 0 TO H - 1
100     FOR X = 0 TO W - 1
110         cr = (X - 50) / 20.0
120         ci = (Y - 12) / 10.0
130         zr = 0: zi = 0: i = 0
140         FOR i = 0 TO 254
150             temp = zr * zr - zi * zi + cr
160             zi = 2 * zr * zi + ci
170             zr = temp
180             IF (zr * zr + zi * zi >= 4) THEN EXIT FOR
190         NEXT i
200         IF i >= 255 THEN
210             R = 0: G = 0: B = 0
220         ELSE
230             R = palette(i,0)
240             G = palette(i,1)
250             B = palette(i,2)
260         ENDIF
270         PRINT BGRGB$(R,G,B);" ";
280     NEXT X
290     PRINT RESET$
300 NEXT Y
310 PRINT RESET$
320 END
