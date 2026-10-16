    10 REM Slot Machine
    20 REM BBC Game Version 
    30 REM (c) 2025 Shaun Lindsley
    40 REM The Slot Machine Simulation Jam
    60 MODE 7
    70 VDU23;8202;0;0;0; : REM Hide Cursor
    80 *FX200,3
    90 *FX15,0
   100 DIM HOLD%(2)
   110 DIM MOTOR%(2)
   120 DIM PRIZE%(12)
   130 DIM REELS%(2,2)
   140 DIM SYMBOL$(15,3)
   150 DIM WINNING%(15)
   160 PRINTTAB(11,12);"INITIALISING DATA";
   170 PROCInitialise
   180 CASH%=500
   190 PROCLayout
   220 REPEAT 
   230   CASH%=500         
   240   GamesPlayed%=0 : HighestWin%=0
   250   NumberWins%=0  : NumberLosses%=0
   260   MoneyWon%=0    : MoneyLost%=0
   270   HOLD%(0) = 0 : HOLD%(1) = 0 : HOLD%(2) = 0
   320   PROCInput
   330   REPEAT
   340     CASH% = CASH% - 10
   350     GamesPlayed% = GamesPlayed% + 1
   360     MoneyLost% = MoneyLost% + 10
   370     MONEY$ = FNMoneyToString(CASH%)
   380     PRINTTAB(8,22);"CASH"FNFormatString(27,MONEY$)
   390     PROCReelMotors
   400     PROCSpinAllReels
   410     HOLD%(0)=0 : HOLD%(1)=0 : HOLD%(2)=0 
   420     IF FNWin(FALSE) PROCGamble ELSE IF RND(4)=1 PROCNudge ELSE IF RND(4)=1 PROCHold
   430     IF CASH% > 0 PROCInput
   440   UNTIL CASH% = 0
   450   PROCStatistics
   460 UNTIL FALSE 
   500 REM Initialise Data
   510 DEF PROCInitialise
   520   RESTORE 4010 : REM *** Fruit Data ***
   530   FOR I%=0 TO 15
   540     FOR J%=2 TO 0 STEP -1
   550       FOR K%=0 TO 5
   560         READ A% : REM Fruit Data
   570         SYMBOL$(I%,J%) = SYMBOL$(I%,J%)+CHR$A% 
   580       NEXT
   590     NEXT
   600   NEXT
   610   RESTORE 5010 : REM *** Winning Line Data ***
   620   FOR I% = 0 TO 15
   630     READ A% : WINNING%(I%) = A% 
   640   NEXT       
   650   RESTORE 5210 : REM *** Prize Money Data ***
   660   FOR I% = 0 TO 12  
   670     READ A% : PRIZE%(I%) = A%
   680   NEXT
   690   REM Randomise starting reel symbols
   700   FOR R%=0 TO 2 : REM Reel Number
   710     FOR J%=0 TO 2 : REM Reel Symbol Offset
   720       REELS%(R%,J%) = RND(16) - 1 : REM RND(X) = 1 TO X
   730     NEXT
   740   NEXT
   750 ENDPROC
   800 REM Statistics
   810 DEF PROCStatistics
   820 CLS
   830 PRINTTAB(13,0);CHR$147;"|<$| _|l0,|,"
   840 PRINTTAB(13,1);CHR$147;"s{5";CHR$255;"p*";CHR$255;"z% ";CHR$255
   850 PRINTTAB(6,2);CHR$146;"h|0x4x<th|,$|4|(l<$|th4|<$"
   860 PRINTTAB(6,3);CHR$146;"j";CHR$255;"""j5";CHR$255;"7";CHR$255;"j";CHR$255;"p0";CHR$255;"7";CHR$255;"_zu0";CHR$255;"5k5";CHR$255;"w0"
   870 PRINTTAB(19,4);"SIMULATION JAM"
   880 PRINTTAB(13,6);CHR$141;CHR$129;"STATISTICS"
   890 PRINTTAB(13,7);CHR$141;CHR$129;"STATISTICS"
   900 PRINTTAB(4,10);CHR$(131);"Games Played"FNFormatNumber(35,GamesPlayed%)
   910 PRINTTAB(4,12);CHR$(131);"Number of Wins"FNFormatNumber(35,NumberWins%)
   920 PRINTTAB(4,14);CHR$(131);"Number of Losses"FNFormatNumber(35,NumberLosses%)
   930 PRINTTAB(4,16);CHR$(131);"Money Won"FNFormatString(35,FNMoneyToString(MoneyWon%))
   940 PRINTTAB(4,18);CHR$(131);"Money Lost"FNFormatString(35,FNMoneyToString(MoneyLost%))
   950 PRINTTAB(4,20);CHR$(131);"Highest Win"FNFormatString(35,FNMoneyToString(HighestWin%))
   960 PRINTTAB(6,23);CHR$133;"Press SPACE BAR to continue"
   970 REPEAT : UNTIL GET=32 : *FX15,1
   980 PROCLayout
   990 ENDPROC
  1000 REM Winning Information
  1010 DEF PROCWinningInfo
  1020 CLS
  1030 PRINTTAB(13,0);CHR$149;"|<$| _|l0,|,"
  1040 PRINTTAB(13,1);CHR$149;"s{5";CHR$255;"p*";CHR$255;"z% ";CHR$255
  1050 PRINTTAB(6,2);CHR$150;"h|0x4x<th|,$|4|(l<$|th4|<$"
  1060 PRINTTAB(6,3);CHR$150;"j";CHR$255;"""j5";CHR$255;"7";CHR$255;"j";CHR$255;"p0";CHR$255;"7";CHR$255;"_zu0";CHR$255;"5k5";CHR$255;"w0"
  1070 PRINTTAB(19,4);"SIMULATION JAM"
  1100 PRINTTAB(4,6);CHR$(134);"3x Lucky Blue Sevens"FNFormatString(35,"`70.00")
  1110 PRINTTAB(4,7);CHR$(131);"3x Bars"FNFormatString(35,"`40.00")
  1120 PRINTTAB(4,8);CHR$(131);"3x Bells"FNFormatString(35,"`20.00")
  1130 PRINTTAB(4,9);CHR$(131);"3x Acorns"FNFormatString(35,"`15.00")
  1140 PRINTTAB(4,10);CHR$(131);"3x Diamonds"FNFormatString(35,"`10.00")
  1150 PRINTTAB(4,11);CHR$(131);"3x Water Melons"FNFormatString(35,"`7.00")
  1160 PRINTTAB(4,12);CHR$(130);"3x Pink Sevens"FNFormatString(35,"`5.00")
  1170 PRINTTAB(4,13);CHR$(130);"3x Hearts"FNFormatString(35,"`5.00")
  1180 PRINTTAB(4,14);CHR$(130);"3x Plums"FNFormatString(35,"`4.00")
  1190 PRINTTAB(4,15);CHR$(130);"3x Green Apples"FNFormatString(35,"`3.00")
  1200 PRINTTAB(4,16);CHR$(130);"3x Strawberries"FNFormatString(35,"`3.00")
  1210 PRINTTAB(4,17);CHR$(129);"3x Oranges"FNFormatString(35,"`2.40")
  1220 PRINTTAB(4,18);CHR$(129);"3x Broken Hearts"FNFormatString(35,"`2.00")
  1230 PRINTTAB(4,19);CHR$(129);"3x Red Apples"FNFormatString(35,"`2.00")
  1240 PRINTTAB(4,20);CHR$(129);"3x Lemons"FNFormatString(35,"`1.20")
  1250 PRINTTAB(4,21);CHR$(129);"3x Cherries"FNFormatString(35,"`1.00")
  1260 PRINTTAB(6,23);CHR$133;"Press SPACE BAR to continue"
  1270 REPEAT : UNTIL GET=32 : *FX15,1
  1280 PROCLayout
  1290 ENDPROC
  1300 REM Layout
  1310 DEF PROCLayout  
  1320 CLS
  1330 PRINTTAB(14,0);CHR$129;"LUCKY"
  1340 PRINTTAB(14,1);CHR$149;"*/'k5"
  1350 PRINTTAB(11,2);CHR$149;"*/'k5~7/'k5"
  1360 PRINTTAB(12,3);CHR$150;"_~?)/%_~?!"
  1370 PRINTTAB(12,4);CHR$150;"*/%   */%"
  1380 PRINTTAB(5,5);CHR$151;"xwsssssssssssssssssss{t";CHR$145;"_p"
  1390 PRINTTAB(5,6);CHR$151;"5";TAB(22);CHR$151;"j";CHR$145;"o";CHR$255;"%";CHR$131;"`70.00"
  1400 PRINTTAB(5,7);CHR$151;"5";TAB(22);CHR$151;"j";CHR$147;" 5";CHR$131;" `40.00"
  1410 PRINTTAB(5,8);CHR$151;"5";TAB(22);CHR$151;"j";CHR$147;" 5";CHR$131;" `20.00"
  1420 PRINTTAB(5,9);CHR$151;"5";TAB(22);CHR$151;"j";CHR$147;" 5";CHR$131;" `15.00"
  1430 PRINTTAB(5,10);CHR$145;"7";TAB(22);CHR$145;"k";CHR$147;" 5";CHR$131;" `10.00"
  1440 PRINTTAB(5,11);CHR$145;"5";TAB(22);CHR$145;"j";CHR$147;" 5";CHR$131;"  `7.00"
  1450 PRINTTAB(5,12);CHR$145;"5";TAB(22);CHR$145;"j";CHR$147;" 5";CHR$131;"  `5.00"
  1460 PRINTTAB(5,13);CHR$145;"5";TAB(22);CHR$145;"j";CHR$147;" 5";CHR$131;"  `4.00"
  1470 PRINTTAB(5,14);CHR$145;"u";TAB(22);CHR$145;"z";CHR$147;" 5";CHR$131;"  `3.00"
  1480 PRINTTAB(5,15);CHR$151;"5";TAB(22);CHR$151;"j";CHR$147;" 5";CHR$131;"  `2.40"
  1490 PRINTTAB(5,16);CHR$151;"5";TAB(22);CHR$151;"j||5";CHR$131;"  `2.00"
  1500 PRINTTAB(5,17);CHR$151;"5";TAB(22);CHR$151;"j";CHR$131;"     `1.20"
  1510 PRINTTAB(5,18);CHR$151;"5";TAB(22);CHR$151;"j";CHR$131;"     `1.00"
  1520 PRINTTAB(5,19);CHR$151;"```````````````````````";
  1530 MONEY$ = FNMoneyToString(CASH%)
  1540 PRINTTAB(5,21);CHR$151;"<,,,,,,,,,,,,,,,,,,,,,l";
  1550 PRINTTAB(5,22);CHR$151;"5";CHR$135;"CASH"FNFormatString(27,MONEY$);CHR$151;"j"
  1560 PRINTTAB(5,23);CHR$151;"-,,,,,,,,,,,,,,,,,,,,,.";
  1570 PROCDrawInitialReels
  1575 FOR R%=0 TO 2
  1576   IF HOLD%(R%) = 1 PRINTTAB(7+R%*7,20);CHR$137;CHR$129;"HELD";CHR$137
  1579 NEXT
  1580 ENDPROC
  1600 REM Calculate number of spins for each Reel Motors
  1610 REM 3 Reel Motors, R0 = (10-25), R1 = R0+(5-10), R2 = R1+(5-10)
  1620 DEF PROCReelMotors
  1630   MOTOR%(0) = 5 + RND(10)
  1640   MOTOR%(1) = 5 + RND(7) + MOTOR%(0)
  1650   MOTOR%(2) = 5 + RND(5) + MOTOR%(1)
  1660   FOR R% = 0 TO 2
  1670     IF (HOLD%(R%) = 1) MOTOR%(R%) = 0
  1680   NEXT
  1690 ENDPROC
  1700 REM Spin Reels
  1710 DEF PROCSpinAllReels
  1720   SOUND &10,-5,3,200 : REM Sound of the Reel Motors
  1730   REPEAT
  1740     FOR R%=0 TO 2
  1750       IF MOTOR%(R%) > 0 PROCSpinReelDown
  1760       IF MOTOR%(R%) = 1 SOUND &12,1,10,10 : REM Reel stopping sound
  1770     NEXT
  1780     PROCDrawReels
  1790     FOR R% = 0 TO 2
  1800       IF MOTOR%(R%) > 0 MOTOR%(R%) = MOTOR%(R%) - 1
  1810     NEXT   
  1820   UNTIL MOTOR%(0) + MOTOR%(1) + MOTOR%(2) = 0 
  1830   SOUND &10,0,0,1 : SOUND &12,0,0,1 : REM Stop Sound
  1840   VDU26
  1850 ENDPROC
  1900 REM Spin Reel Down R%
  1910 DEF PROCSpinReelDown
  1920   REELS%(R%,2) = REELS%(R%,1)
  1930   REELS%(R%,1) = REELS%(R%,0)
  1940   REELS%(R%,0) = RND(16) - 1 : REM RND(X) = 1 TO X
  1950 ENDPROC
  2000 REM Spin Reel Up R%
  2010 DEF PROCSpinReelUp
  2020   REELS%(R%,0) = REELS%(R%,1)
  2030   REELS%(R%,1) = REELS%(R%,2)
  2040   REELS%(R%,2) = RND(16) - 1 : REM RND(X) = 1 TO X
  2050 ENDPROC
  2100 REM Draw Reels
  2110 DEF PROCDrawReels
  2120   FOR H%=0 TO 3   : REM Height of symbol
  2130     FOR R%=0 TO 2
  2140       IF MOTOR%(R%) > 0 VDU28,7*(R%+1),18,7*(R%+1)+5,6,30,11 : PRINT SYMBOL$(REELS%(R%,0),H%) : REM PROCDrawSymbol
  2150     NEXT
  2160   NEXT
  2170 ENDPROC
  2171REM 2200 REM Draw Partial Symbol
  2172REM 2210 DEF PROCDrawSymbol
  2173REM 2220   VDU28,7*(R%+1),18,7*(R%+1)+5,6,30,11
  2174REM 2230   PRINT SYMBOL$(REELS%(R%,0),H%) 
  2175REM 2240 ENDPROC
  2250 REM Draw Initial symbols row by row
  2260 DEF PROCDrawInitialReels
  2270   FOR K%=2 TO 0 STEP -1        
  2280     FOR H%=0 TO  3     : REM Height of symbol
  2290       FOR R%=0 TO 2
  2300         VDU28,7*(R%+1),18,7*(R%+1)+5,6,30,11
  2310         PRINT SYMBOL$(REELS%(R%,K%),H%) 
  2320       NEXT
  2330     NEXT
  2340   NEXT
  2350   VDU 26
  2360 ENDPROC
  2400 DEF PROCMoveHandle
  2410   FOR Y%=0 TO 6
  2420     PROCHandle : FOR X%=0 TO 100 : NEXT
  2430   NEXT
  2440   FOR Y%=6 TO 0 STEP -1
  2450     PROCHandle : FOR X%=0 TO 100 : NEXT
  2460   NEXT
  2470 ENDPROC
  2480 DEF PROCHandle
  2483   PRINTTAB(29,Y%+4);CHR$145;"   ";CHR$131;
  2485   PRINTTAB(29,Y%+5);CHR$145;"_p ";CHR$131;
  2487   PRINTTAB(29,Y%+6);CHR$145;"o";CHR$255;"%";CHR$131;
  2489   PRINTTAB(29,Y%+7);CHR$147;" 5 ";CHR$131;
  2490 ENDPROC
  2500 REM Input SPACEBAR, S for Stats and I for winning info
  2510 DEF PROCInput
  2530   FOR R%=0 TO 2
  2535    IF HOLD%(R%) = 0 THEN PRINTTAB(7+R%*7,20);SPC(7);
  2537   NEXT
  2538   MONEY$ = FNMoneyToString(CASH%)
  2539   T%=0
  2540   REPEAT
  2550     PRINTTAB(33,20);CHR$136;CHR$130;"START";
  2560     PRINTTAB(29,0);CHR$134;"STATS/INFO";
  2570     PRINTTAB(29,1);CHR$150;"`     `";
  2580     K% = INKEY(100)
  2585     T% = T% EOR 1
  2590     IF K%=73 PROCWinningInfo
  2600     IF K%=83 PROCStatistics
  2605     IF T%=0 PRINTTAB(8,22);"CASH"FNFormatString(27,MONEY$); ELSE PRINTTAB(8,22);"   SPACE TO SPIN   ";
  2610   UNTIL K%=32
  2615   PROCMoveHandle
  2620   PRINTTAB(33,20);CHR$137;CHR$130;"START"
  2630 ENDPROC
  2640 REM Win (N% = Coming from Nudge function)
  2650 DEF FNWin(N%)
  2660 R%= (REELS%(0,1) = REELS%(1,1) AND REELS%(1,1) = REELS%(2,1))
  2670 IF R% = TRUE: = TRUE
  2680 IF N% = FALSE NumberLosses% = NumberLosses%+1
  2690 = FALSE
  2700 REM Nudge Feture
  2710 DEF PROCNudge
  2720  PROCNudgeSkill
  2730  PRINTTAB(6,20);CHR$136;CHR$130;"NUDGE  NUDGE  NUDGE"
  2740  T%=0
  2750  REPEAT
  2760     *FX15,1
  2770     K% = INKEY(100)
  2780     T% = T% EOR 1
  2785     IF K%=96 K%=35 : REM Fix for BeebEm Shift 3
  2790     IF K%>48 AND K%<52 AND N%>0 PROCNudgeReelDown(K%-49) : PRINTTAB(2,16-N%);CHR$135 : N% = N%-1 : PRINTTAB(2,16-N%);CHR$130 : IF FNWin(TRUE) NumberLosses% = NumberLosses%-1 : PROCGamble : N%=0
  2800     IF K%>32 AND K%<36 AND N%>0 PROCNudgeReelUp(K%-33)   : PRINTTAB(2,16-N%);CHR$135 : N% = N%-1 : PRINTTAB(2,16-N%);CHR$130 : IF FNWin(TRUE) NumberLosses% = NumberLosses%-1 : PROCGamble : N%=0
  2810     IF T%=0 PRINTTAB(8,22);"     NUDGE NOW     "; ELSE PRINTTAB(8,22);" YOU HAVE ";N%;" NUDGE  ";
  2820     IF T%=1 AND N%>1 PRINTTAB(25,22);"S";
  2830   UNTIL K% = 32 OR N%=0
  2840   PRINTTAB(6,20);SPC(22);
  2850   PRINTTAB(0,10);"    "'"    "'"    "'"    "'"    "'"    "
  2860   MONEY$ = FNMoneyToString(CASH%)
  2870   PRINTTAB(8,22);"CASH"FNFormatString(27,MONEY$)
  2880 ENDPROC
  2900 REM Nudge Skill (N% = Number of Nudges)
  2910 DEF PROCNudgeSkill
  2920   N%=1
  2930   PRINTTAB(0,10);CHR$133;"N"CHR$135;"6"';CHR$133;"U"CHR$135;"5"';CHR$133;"D"CHR$135;"4"';CHR$133;"G"CHR$135;"3"';CHR$133;"E"CHR$135;"2"';CHR$133;"S"CHR$135;"1"
  2940   PRINTTAB(8,22);CHR$136;"SPACE TO COLLECT ";CHR$137                          
  2950   REPEAT
  2960     SOUND &11,1,N%*10,5
  2970     PRINTTAB(2,16-N%);CHR$135 
  2980     N%=RND(6)
  2990     PRINTTAB(2,16-N%);CHR$130
  3000   UNTIL INKEY(10) = 32
  3010   SOUND &11,1,0,1
  3020 ENDPROC
  3030 REM Nudge Reel (R%) Down
  3040 DEF PROCNudgeReelDown(R%)
  3050   PROCSpinReelDown
  3060   VDU28,7*(R%+1),18,7*(R%+1)+5,6
  3070   FOR H%=0 TO 3   : REM Height of symbol
  3080     VDU 30,11
  3090     PRINT SYMBOL$(REELS%(R%,0),H%) 
  3100   NEXT
  3110   VDU26
  3120 ENDPROC
  3130 REM Nudge Reel (R%) Up
  3135 REM Needs semicolon on end of Print to stop line feed
  3140 DEF PROCNudgeReelUp(R%)
  3150   PROCSpinReelUp
  3160   VDU28,7*(R%+1),18,7*(R%+1)+5,6,31,0,12,10
  3170   FOR H%=3 TO 0 STEP-1
  3180     PRINT SYMBOL$(REELS%(R%,0),H%);
  3190   NEXT
  3200   VDU26
  3210 ENDPROC
  3300 REM Hold Feature
  3310 DEFPROCHold
  3320   FOR I%=0 TO 2
  3330     PRINTTAB(7+I%*7,20);CHR$136;CHR$130;"HOLD";CHR$137;
  3340   NEXT
  3350   T%=0
  3360   REPEAT
  3370     *FX15,1
  3380     K% = INKEY(100)
  3390     T% = T% EOR 1
  3400     IF T%=0 PRINTTAB(8,22);"  1/2/3 TO TOGGLE  "; ELSE PRINTTAB(8,22);"  OR SPACE TO END  ";
  3410     R%=-1 
  3420     IF K%>48 AND K%<52 R% = K%-49 : REM Convert to 0,1 or 2
  3430     IF R%>-1 HOLD%(R%) = HOLD%(R%) EOR 1
  3440     IF R%>-1 IF HOLD%(R%) = 0 PRINTTAB(7+R%*7,20);CHR$136;CHR$130;"HOLD";CHR$137
  3450     IF R%>-1 IF HOLD%(R%) = 1 PRINTTAB(7+R%*7,20);CHR$137;CHR$129;"HELD";CHR$137
  3460   UNTIL K% = 32
  3470   MONEY$ = FNMoneyToString(CASH%)
  3480   PRINTTAB(8,22);"CASH"FNFormatString(27,MONEY$)
  3490 ENDPROC
  3500 REM Gamble
  3510 DEFPROCGamble
  3530   PRINTTAB(6,20);SPC(22);
  3540   PRINTTAB(0,10);"    "'"    "'"    "'"    "'"    "'"    "
  3550   PRINTTAB(32,20);CHR$136;CHR$130;"GAMBLE"
  3560   C%=0 : T%=0
  3570   S% = REELS%(0,1)
  3580   I% = WINNING%(S%) : REM Money index
  3590   W% = PRIZE%(I%) : R%=0 : REM Money 18 = 0
  3600   PRINTTAB(33,18-I%);CHR$130
  3610   IF I%=12 PROCCollect(I%) : ENDPROC
  3620   REPEAT
  3630     R%=R% EOR 1 
  3640     IF R%=0 PRINTTAB(33,19-I%);CHR$129 : PRINTTAB(33,17-I%);CHR$131
  3650     IF R%=1 PRINTTAB(33,17-I%);CHR$129 : PRINTTAB(33,19-I%);CHR$131
  3660     SOUND &12,2,10,5
  3670     K% = INKEY(10)
  3680     IF (K%=71 AND R%=0) I%=I%-1 
  3690     IF (K%=71 AND R%=1) I%=I%+1 : PRINTTAB(33,18-I%);CHR$130
  3700     C%=C%+1 : IF C% MOD 10 = 0 T% = T% EOR 1
  3710     IF T%=0 PRINTTAB(8,22);"     TAKE CASH     ";     
  3720     IF T%=1 PRINTTAB(8,22);"  OR GAMBLE CASH   "; 
  3730   UNTIL K%=67 OR I%=12 OR (K%=71 AND R%=0)
  3740   SOUND &12,0,0,1
  3750   PRINTTAB(33,18-I%-1);CHR$131
  3760   PRINTTAB(33,18-I%+1);CHR$131
  3765   PRINTTAB(32,20);SPC(8);
  3770   IF I% = -1 ENDPROC
  3780   PROCCollect(I%)
  3790 ENDPROC
  3800 REM Collect Winnings
  3810 DEF PROCCollect(I%)
  3815   PRINTTAB(32,20);SPC(8);
  3820   SOUND &12,3,10,100
  3830   W% = PRIZE%(I%) 
  3840   MONEY$ = FNMoneyToString(W%)
  3850   PRINTTAB(8,22);"YOU'VE WON"FNFormatString(27,MONEY$)
  3860   PRINTTAB(33,18-I%);CHR$131
  3870   NumberWins% = NumberWins% + 1
  3880   IF HighestWin% < W% HighestWin% = W%
  3890   MoneyWon% = MoneyWon% + W%
  3900   CASH% = CASH% + W%
  3910   finishtime=TIME+500
  3920   REPEAT UNTIL TIME>=finishtime
  3930   MONEY$ = FNMoneyToString(CASH%)
  3940   PRINTTAB(8,22);"CASH"FNFormatString(27,MONEY$)
  3950 ENDPROC
  3960 REM FN Formatting Functions
  3970 DEF FNFormatNumber(P%,M%) =FNFormatString(P%,STR$(M%))
  3980 DEF FNFormatString(P%,M$) =STRING$((P%-POS-LENM$),".")+M$
  3990 DEF FNMoneyToString(C%)   ="`" + STR$(C%DIV100)+"."+RIGHT$("0"+STR$(C%MOD100),2)
  4000 REM Fruit 1 Cherry `1.00
  4010 DATA &92,&20,&E0,&26,&E7,&20 : REM Green
  4020 DATA &91,&68,&77,&34,&7E,&79 : REM Red
  4030 DATA &91,&20,&A3,&20,&22,&21 : REM Red
  4050 REM Fruit 2 Lemon `1.20
  4060 DATA &93,&20,&E0,&F0,&B0,&20 : REM Yellow
  4070 DATA &93,&68,&FF,&FF,&FF,&34 : REM Yellow
  4080 DATA &93,&22,&6F,&FF,&3F,&21 : REM Yellow
  4100 REM Fruit 3 Red Apple `2.00
  4110 DATA &92,&A2,&A9,&F4,&20,&20 : REM Green
  4120 DATA &91,&E8,&EB,&FF,&FF,&B4 : REM Red
  4130 DATA &91,&AA,&F5,&EF,&FF,&A5 : REM Red
  4150 REM Fruit 4 Broken Heart `2.00
  4160 DATA &91,&20,&70,&20,&70,&20 : REM Red
  4170 DATA &91,&6A,&77,&6E,&FF,&35 : REM Red
  4180 DATA &91,&20,&2B,&79,&27,&20 : REM Red
  4200 REM Fruit 5 Orange `2.40
  4210 DATA &92,&20,&A8,&74,&20,&20 : REM Green
  4220 DATA &93,&E8,&FF,&FF,&FF,&B4 : REM Yellow
  4230 DATA &93,&AA,&FF,&FF,&FF,&A5 : REM Yellow
  4250 REM Fruit 6 Stawberry `3.00
  4260 DATA &92,&A8,&A9,&F4,&20,&20 : REM Green
  4270 DATA &91,&EA,&FB,&F7,&F7,&B5 : REM Red
  4280 DATA &91,&20,&AB,&FE,&A7,&20 : REM Red
  4300 REM Fruit 7 Green Apple `3.00
  4310 DATA &92,&A2,&A9,&F4,&20,&20 : REM Green
  4320 DATA &92,&E8,&EB,&FF,&FF,&B4 : REM Green
  4330 DATA &92,&AA,&F5,&EF,&FF,&A5 : REM Green
  4350 REM Fruit 8 Plum `4.00
  4360 DATA &92,&20,&20,&F8,&AC,&20 : REM Green 
  4370 DATA &95,&E8,&FF,&FF,&FF,&B4 : REM Magenta
  4380 DATA &95,&AA,&FF,&FF,&FF,&A5 : REM Magenta
  4400 REM Fruit 9 Heart `5.00
  4410 DATA &91,&20,&70,&20,&70,&20 : REM Red
  4420 DATA &91,&6A,&FF,&FF,&FF,&35 : REM Red
  4430 DATA &91,&20,&2B,&FF,&27,&20 : REM Red
  4450 REM Fruit 10 Melon $7.00
  4460 DATA &92,&E0,&7C,&BF,&A9,&B0 : REM Green
  4470 DATA &92,&FF,&FF,&B1,&A4,&B9 : REM Green
  4480 DATA &92,&A2,&AF,&FD,&B8,&A1 : REM Green
  4500 REM Fruit 11 Diamond `10.00
  4510 DATA &96,&20,&70,&70,&70,&20 : REM Cyan
  4520 DATA &96,&66,&73,&73,&73,&39 : REM Cyan 
  4530 DATA &96,&20,&2B,&FF,&27,&20 : REM Cyan
  4550 REM Fruit 12 Acorn `15.00
  4560 DATA &92,&9A,&F8,&FF,&F4,&99 : REM Green
  4570 DATA &92,&9A,&AF,&AF,&AF,&99 : REM Green
  4580 DATA &91,&A2,&EF,&FF,&BF,&B1 : REM Red
  4600 REM Fruit 13 Bell `20.00
  4610 DATA &93,&20,&E0,&7C,&30,&20 : REM Yellow 
  4620 DATA &93,&E0,&FF,&FF,&FF,&30 : REM Yellow
  4630 DATA &93,&A3,&E3,&73,&33,&A3 : REM Yellow
  4650 REM Fruit 14 Bar `40.00
  4660 DATA &94,&AC,&AC,&AC,&AC,&AC : REM Blue
  4670 DATA &97,&A4,&42,&41,&52,&A8 : REM White
  4680 DATA &94,&AC,&AC,&AC,&AC,&AC : REM Blue
  4700 REM Fruit 15 Seven `5.00
  4710 DATA &95,&20,&FC,&FC,&AC,&FC : REM Magenta
  4720 DATA &95,&20,&20,&E0,&FC,&A7 : REM Magenta
  4730 DATA &95,&20,&20,&FF,&FF,&20 : REM Magenta
  4750 REM Fruit 16 Seven `70.00
  4760 DATA &96,&20,&FC,&FC,&AC,&FC : REM Cyan
  4770 DATA &96,&20,&20,&E0,&FC,&A7 : REM Cyan
  4780 DATA &96,&20,&20,&FF,&FF,&20 : REM Cyan
  5000 REM Winning Line
  5010 DATA 0  : REM 1  Cherry       
  5020 DATA 1  : REM 2  Lemon        
  5030 DATA 2  : REM 3  Red Apples   
  5040 DATA 2  : REM 4  Broken Heart 
  5050 DATA 3  : REM 5  Oranges      
  5060 DATA 4  : REM 6  Stawberrys   
  5070 DATA 4  : REM 7  Green Apple  
  5080 DATA 5  : REM 8  Plums        
  5090 DATA 6  : REM 9  Hearts       
  5100 DATA 7  : REM 10 Watermelon   
  5110 DATA 8  : REM 11 Diamonds    
  5120 DATA 9  : REM 12 Acorns      
  5130 DATA 10 : REM 13 Bells       
  5140 DATA 11 : REM 14 Bars        
  5150 DATA 6  : REM 15 Lucky Magenta 7's    
  5160 DATA 12 : REM 16 Lucky Blue 7's    
  5200 REM Prize Money
  5210 DATA 100  : REM  `1.00
  5220 DATA 120  : REM  `1.20
  5230 DATA 200  : REM  `2.00
  5240 DATA 240  : REM  `2.40
  5250 DATA 300  : REM  `3.00
  5260 DATA 400  : REM  `4.00
  5270 DATA 500  : REM  `5.00
  5280 DATA 700  : REM  `7.00
  5290 DATA 1000 : REM `10.00
  5300 DATA 1500 : REM `15.00
  5310 DATA 2000 : REM `20.00
  5320 DATA 4000 : REM `40.00
  5330 DATA 7000 : REM `70.00 MAX