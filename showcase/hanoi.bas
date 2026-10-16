    10       ON ERROR IF ERR = 17 CHAIN @lib$+"../examples/tools/touchide"ELSE MODE 3: PRINT REPORT$: END
    20       REM . "THE TOWERS OF HANOI"
    30       REM . R.T.RUSSELL, 08-08-1982: BBC BASIC
    40       
    50       DIM DISC$(13),SIZE(3)
    60       FOR DISC = 1 TO 13
    70         DISC$(DISC) = STRING$(DISC," ") + STR$DISC + STRING$(DISC," ")
    80         IF DISC >= 10 DISC$(DISC) = MID$(DISC$(DISC),2)
    90         REM BBC TRUE=-1: 128+DISC-(DISC>7) -> 7=white 135, 8=red 137 (SDL)
   100         DISC$(DISC) = CHR$17 + CHR$(128 + DISC - (DISC>7)) + DISC$(DISC) + CHR$17 + CHR$128
   110       NEXT DISC
   120       
   130       MODE 3
   140       INPUT "Number of discs (1-13): "F
   150       IF F>13 RUN
   160       FOR N = F TO 1 STEP -1: PROCPUT(N,1): NEXT
   170       PRINT TAB(0,1)"Press SPACE to start": A = GET: PRINT TAB(0,1)STRING$(20," ")
   180       OFF
   190       PROCHANOI(F,1,2,3)
   200       PRINTTAB(0,22);
   210       REPEAT WAIT 1: UNTIL FALSE
   220       ;
   230       DEF PROCHANOI(A,B,C,D) IF A = 0 ENDPROC
   240       PROCHANOI(A - 1,B,D,C)
   250       PROCTAKE(A,B): PROCPUT(A,C): *REFRESH
   260       PROCHANOI(A - 1,D,C,B)
   270       ENDPROC
   280       ;
   290       DEF PROCPUT(DISC,PILE)
   300       PRINTTAB(13 + 26 * (PILE - 1) - DISC,20 - SIZE(PILE))DISC$(DISC);
   310       SIZE(PILE) = SIZE(PILE) + 1
   320       ENDPROC
   330       ;
   340       DEF PROCTAKE(DISC,PILE)
   350       SIZE(PILE) = SIZE(PILE) - 1
   360       PRINTTAB(13 + 26 * (PILE - 1) - DISC,20 - SIZE(PILE))STRING$(2 * DISC + 1," ");
   370       ENDPROC
