REM mouse_click_letter.bas — verify MOUSE coords + VDU 5 PRINT
REM Left-click: print "X" at pointer. Right-click: clear. Esc/close to quit.
REM Top line shows live X%, Y%, B% in OS graphics units.

ON ERROR IF ERR=17 END ELSE PRINT REPORT$:END
MODE 8
GCOL 0,7
VDU 4
PRINT TAB(0,0);"Left-click=X  Right=CLS  (Esc closes)"
*REFRESH ON
REPEAT
  MOUSE X%,Y%,B%
  VDU 4
  PRINT TAB(0,1);"X%=";X%;" Y%=";Y%;" B%=";B%;"   ";
  IF (B% AND 1) <> 0 THEN
    VDU 5
    MOVE X%,Y%
    PRINT "X";
    VDU 4
    *REFRESH
    REPEAT
      MOUSE A%,C%,B%
      WAIT 1
    UNTIL (B% AND 1)=0
  ENDIF
  IF (B% AND 2) <> 0 THEN
    CLS
    PRINT TAB(0,0);"Left-click=X  Right=CLS  (Esc closes)"
    *REFRESH
    REPEAT MOUSE A%,C%,B%:WAIT 1:UNTIL (B% AND 2)=0
  ENDIF
  *REFRESH
  WAIT 1
UNTIL FALSE
