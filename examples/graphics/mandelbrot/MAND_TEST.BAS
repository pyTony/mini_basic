10 W% = 80
20 H% = 25
30 Z$ = ".,'~=+:;*%&$OXB#@ "
35 PRINT RESET$;RGB$(255,255,255)
40 FOR Y% = 0 TO H% - 1
50     FOR X% = 0 TO W% - 1
60         REM Map screen coordinates TO complex plane
70         cr = (X% - 50) / 20.0
80         ci = (Y% - 12) / 10.0
90         zr = 0: zi = 0: i% = 0
100         REM Mandelbrot iteration loop (Max 256 iterations)
110         WHILE (zr * zr + zi * zi < 4) AND (i% < 255)
120             temp = zr * zr - zi * zi + cr
130             zi = 2 * zr * zi + ci
140             zr = temp
150             i% = i% + 1
160         ENDWHILE
170         REM Tulostetaan väri iteraation mukaan
180         IF i% = 255 THEN
190             PRINT RGB$(0,0,0);" ";
200         ELSE
210             REM Kertoimilla (0.1, 0.2, 0.3) säädetään värien vaihtumisnopeutta
220             R% = INT(127.5 * (1 + SINRAD(i% * 10)))
230             G% = INT(127.5 * (1 + SINRAD(i% * 15)))
240             B% = INT(127.5 * (1 + SINRAD(i% * 20)))
250         ENDIF
255         PRINT R%,G%,B%
260         PRINT RGB$(R%,G%,B%);
265         PRINT "#";
270     NEXT X%
280 NEXT Y%
290 PRINT RESET$;RGB$(255,255,255)
