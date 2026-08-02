REM Unusual mouse-following clock (R.T.Russell) — text port for mini_basic.
REM Spring x4 per glyph: same math as BBCSDL; extra steps keep the date ring
REM circular on slower hosts when the mouse is still (TIME still advances).
ON ERROR OSCLI "REFRESH ON" : IF ERR=17 END ELSE MODE 3 : PRINT REPORT$ : END
VDU 23,22,640;480;8,16,16,128
DIM C$(50),X%(50),Y%(50)
VDU 5
*REFRESH OFF
REPEAT
  CLS
  MOUSE X%,Y%,B%
  Time$ = TIME$
  H% = VAL(MID$(Time$,17))
  M% = VAL(MID$(Time$,20))
  S% = VAL(MID$(Time$,23))
  FOR I% = 1 TO 50
    MOVE X%(I%),Y%(I%) : PRINT C$(I%);
    CASE TRUE OF
      WHEN I%<13: R=200 : T=I%*30 : C$(I%)=STR$I%
      WHEN I%>12 AND I%<16: R=(I%-12)*36 : T=H%*30+M%/2 : C$(I%)="."
      WHEN I%>15 AND I%<20: R=(I%-15)*36 : T=M%*6+S%/10 : C$(I%)="."
      WHEN I%>19 AND I%<26: R=(I%-20)*36 : T=S%*6 : C$(I%)="."
      WHEN I%>25: R=300 : T=I%*14-(TIME/4)MOD360 : C$(I%)=MID$(Time$,I%-25,1)
    ENDCASE
    FOR Z%=1 TO 4
      X%(I%) += (X%+R*SIN(RAD(T))-X%(I%)-250)/(1+T/60)
      Y%(I%) += (Y%+R*COS(RAD(T))-Y%(I%)-250)/(1+T/60)
    NEXT Z%
  NEXT
  *REFRESH
  D% = INKEY(4)
UNTIL FALSE
