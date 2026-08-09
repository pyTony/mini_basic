    10 MODE 8
    15 OFF
    20 ORIGIN 640,512
    25 * REFRESH OFF
    30 m1% = 400
    40 REPEAT
    50     CLG
    60     t% = (t%+1) MOD 360
    70     FOR a1% = 0 TO 345 STEP 15
    80         x1% = m1%* SIN(RAD(a1%-t%))
    90         y1% = m1%* COS(RAD(a1%-t%))
   100        PROCbow(1536 * a1%/ 360)
   110        GCOL slot%
   115        CIRCLEFILL x1%,y1%,80
   120        GCOL 0
   125        CIRCLE x1%,y1%,80
   130    NEXT
   135    * REFRESH
   140    REPEAT WAIT 0
   150    UNTIL T% <> TIME
   160    T% = TIME
   170 UNTIL FALSE
   180       DEFPROCbow(N%)
   190         band% = N% DIV 256
   195         slot% = band% + 1
   200         CASE band% OF
   210           WHEN 0: r% = 255:g% = N%MOD 256:b% = 0
   220           WHEN 1: r% = 255 - (N%MOD 256):g% = 255:b% = 0
   230           WHEN 2: r% = 0:g% = 255:b% = N%MOD 256
   240           WHEN 3: r% = 0:g% = 255 - (N%MOD 256):b% = 255
   250           WHEN 4: r% = N%MOD 256:g% = 0:b% = 255
   260           WHEN 5: r% = 255:g% = 0:b% = 255 - (N%MOD 256)
   270           OTHERWISE r% = 128:g% = 128:b% = 128
   280         ENDCASE
   290         COLOR slot%,r%,g%,b%
   300       ENDPROC
