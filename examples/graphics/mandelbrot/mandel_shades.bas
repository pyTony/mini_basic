10 MODE 13: REM Standard text mode
20 W% = 80
30 H% = 25
40 Z$ = ".,'~=+:;*%&$OXB#@ "
50 FOR Y% = 0 TO H% - 1
60     FOR X% = 0 TO W% - 1
70         REM Map screen coordinates TO complex plane
80         cr = (X% - 50) / 20
90         ci = (Y% - 12) / 10
100         zr = 0: zi = 0: i% = 0
110         REM Mandelbrot iteration loop (Max 256 iterations)
120         WHILE (zr * zr + zi * zi < 4) AND (i% < 255)
130             temp = zr * zr - zi * zi + cr
140             zi = 2 * zr * zi + ci
150             zr = temp
160             i% = i% + 1
170         ENDWHILE
180         REM Tulostetaan väri iteraation mukaan
190         IF i% = 255 THEN
200             COLOUR 0: REM Musta keskusta
210             PRINT " ";
220         ELSE
230             COLOUR (i%MOD 15) + 1: REM Kirkkaat värit (1 - 15)
240             PRINT MID$(Z$, i% + 1, 1);: REM Tulostetaan merkki
250         ENDIF
260     NEXT X%
270     PRINT : REM Move TO next line
280 NEXT Y%
