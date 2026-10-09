REM Welcome zap pause probe
REM Runs the letter-row swooshes only. After each zap converges, skips the
REM final invert erase, marks endpoints vs letter target, prints deltas,
REM and waits for a key (Space/any). Escape ends.
REM
REM Run:
REM   python -m mini_basic --dialect bbc --pygame --hold examples/general/welcome_zap_pause.bas
REM Non-interactive endpoint table:
REM   python tools/welcome_zap_probe.py
REM
   10 ON ERROR IF ERR=17 END ELSE MODE 7:REPORT:END
   20 M0=650:M1=500:M2=708:M3=104:M8=5:V%=2
   30 MODE 5
   40 VDU 5
   50 VDU 23,255,255,255,255,255,255,255,255,255
   60 GCOL 0,135
   70 CLG
   80 VDU 18,0,129,24,128;128;1152;896;16,18,0,135,24,256;256;1024;768;16,24,0;0;1278;1022;
   90 PRINT TAB(0,0);"ZAP PAUSE: key=next letter  Esc=quit"
  100 FOR I%=M1 TO M2 STEP M3
  110   PROCSWOOSH(M0)
  120   PROCCOMPARE(M0)
  130   PROCLETTER
  140 NEXT
  150 PRINT TAB(0,1);"Done BBC row. Key to end."
  160 REPEAT UNTIL INKEY(5)=FALSE
  170 END

  200 DEF PROCLETTER
  210 GCOL 0,1:GCOL 0,135
  220 MOVE I%-4,M0+4:PRINT CHR$255;
  230 MOVE I%,M0-28:DRAW I%+56,M0-28
  240 MOVE I%,M0+8:DRAW I%+56,M0+8
  250 MOVE I%-8,M0+4:DRAW I%-8,M0-28
  260 MOVE I%,M0-32:DRAW I%+56,M0-32
  270 MOVE I%+64,M0+4:DRAW I%+64,M0-28
  280 GCOL 0,7:GCOL 0,129
  290 MOVE I%+6,M0+2:PRINT CHR$(ASC("B")-(I%=M2));
  300 ENDPROC

  400 DEF PROCSWOOSH(Y%)
  410 XL%=0:XR%=1272:YD%=0:YU%=1020
  420 U1%=(I%+32-XL%) DIV M8:V1%=(Y%-16-YD%) DIV M8
  430 U2%=(I%+32-XR%) DIV M8:V2%=(Y%-16-YU%) DIV M8
  440 X1%=XL%:X2%=XL%:X3%=XR%:X4%=XR%:Y1%=YD%:Y2%=YU%:Y3%=YD%:Y4%=YU%
  450 PROCPLOT
  460 FOR J0%=1 TO M8
  470   PROCPLOT
  480   X1%=X1%+U1%:X2%=X2%+U1%:X3%=X3%+U2%:X4%=X4%+U2%
  490   Y1%=Y1%+V1%:Y2%=Y2%+V2%:Y3%=Y3%+V1%:Y4%=Y4%+V2%
  500   PROCPLOT
  510 NEXT
  520 REM Intentionally NO final PROCPLOT (would invert-erase the rays).
  530 ENDPROC

  600 DEF PROCPLOT
  610 MOVE X1%-U1%,Y1%-V1%:PLOT 6,X1%,Y1%:MOVE X2%-U1%,Y2%-V2%:PLOT 6,X2%,Y2%
  620 MOVE X3%-U2%,Y1%-V1%:PLOT 6,X3%,Y3%:MOVE X4%-U2%,Y4%-V2%:PLOT 6,X4%,Y4%
  630 ENDPROC

  700 DEF PROCCOMPARE(Y%)
  710 TX%=I%+32:TY%=Y%-16
  720 REM Solid markers: target = yellow-ish (3), ends = black (0)
  730 GCOL 0,3
  740 MOVE TX%-16,TY%:DRAW TX%+16,TY%:MOVE TX%,TY%-16:DRAW TX%,TY%+16
  750 GCOL 0,0
  760 PLOT 69,X1%,Y1%:PLOT 69,X2%,Y2%:PLOT 69,X3%,Y3%:PLOT 69,X4%,Y4%
  770 REM Also solid residual rays to target for eye compare
  780 GCOL 0,1
  790 MOVE X1%,Y1%:DRAW TX%,TY%
  800 MOVE X2%,Y2%:DRAW TX%,TY%
  810 MOVE X3%,Y3%:DRAW TX%,TY%
  820 MOVE X4%,Y4%:DRAW TX%,TY%
  830 PRINT TAB(0,2);"I%=";I%;"  tgt=";TX%;",";TY%
  840 PRINT TAB(0,3);"X1,Y1=";X1%;",";Y1%;" d=";X1%-TX%;",";Y1%-TY%
  850 PRINT TAB(0,4);"X2,Y2=";X2%;",";Y2%;" d=";X2%-TX%;",";Y2%-TY%
  860 PRINT TAB(0,5);"X3,Y3=";X3%;",";Y3%;" d=";X3%-TX%;",";Y3%-TY%
  870 PRINT TAB(0,6);"X4,Y4=";X4%;",";Y4%;" d=";X4%-TX%;",";Y4%-TY%
  880 PRINT TAB(0,7);"U1,V1=";U1%;",";V1%;" U2,V2=";U2%;",";V2%
  890 PRINT TAB(0,8);"key=continue"
  900 *REFRESH
  910 K%=GET
  920 ENDPROC
