10 REM Mandelbrot MODE 9 — solid tiles (RECTANGLE FILL), progressive *REFRESH.
20 MODE 9
30 VDU 20
40 COLOUR 7: COLOUR 128
50 OFF
60 CLG
70 PRINT TAB(0,0);"Mandelbrot M9"
80 TIME = 0
90 XMIN = -2.25: XMAX = 0.75
100 YMIN = -1.35: YMAX = 1.35
110 MAXITER% = 24
120 W% = 640: H% = 512: ST% = 4
130 BW% = ST% * 2: BH% = ST% * 2
140 *REFRESH OFF
150 FOR PY% = 0 TO H% - ST% STEP ST%
160     CY = YMIN + (PY% / (H% - 1)) * (YMAX - YMIN)
170     FOR PX% = 0 TO W% - ST% STEP ST%
180         CX = XMIN + (PX% / (W% - 1)) * (XMAX - XMIN)
190         I% = 0: ZX = 0.0: ZY = 0.0: C% = -1
200         WHILE C% AND (I% < MAXITER%)
210             TEMP = ZX * ZX - ZY * ZY
220             ZY = 2.0 * ZX * ZY + CY
230             ZX = TEMP + CX
240             I% = I% + 1
250             C% = (ZX * ZX + ZY * ZY < 4.0)
260         ENDWHILE
270         IF I% < MAXITER% THEN
280             COL% = (I% MOD 7) + 1
290             GCOL 0, COL%
300             RECTANGLE FILL PX% * 2, PY% * 2, BW%, BH%
310         ENDIF
320     NEXT PX%
330     *REFRESH
340 NEXT PY%
350 *REFRESH ON
360 T = TIME
370 PRINT TAB(0,31);"Done "; T / 100;"s"
380 END
