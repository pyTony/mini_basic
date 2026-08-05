10 REM ROADRACE - road scrolls DOWN toward car; walls snake L/R
20 REM Z/z left, X/x right. Keys on top; stats under car. 10 crashes ends.
30 REM A%(1)=far ahead ... A%(L%)=segment at car.

100 ON ERROR GOTO 9000
110 MODE 0
120 W%=40 : L%=8
130 GOSUB 1000
140 GOTO 200

1000 REM title
1010 CLS
1020 PRINT TAB(5,2);"ROADRACE"
1030 PRINT TAB(3,4);"Keep O between the * walls"
1040 PRINT
1050 PRINT "  Controls: Z/z left, X/x right"
1060 PRINT "  Road comes toward you (scrolls down)."
1070 PRINT "  Walls stop the car. Crash flashes reverse."
1080 PRINT "  10 crashes ends the run."
1090 PRINT
1100 PRINT "  Press any key to start..."
1110 G$=GET$
1120 RETURN

200 REM race init
210 CLS
220 DIM A%(L%)
230 FOR I%=1 TO L% : A%(I%)=8 : NEXT
240 B%=A%(L%)+3 : C%=0 : G%=0
250 BL$=STRING$(W%," ")

260 REM main loop
270 H%=0
280 REM scroll road DOWN (toward car at row L%)
290 FOR I%=L% TO 2 STEP -1
300 J%=I%-1
310 A%(I%)=A%(J%)
320 NEXT
330 REM new segment at top (far); snake L/R
340 N%=10 : R%=RND(N%)
350 A%(1)=A%(2)
360 IF R%<4 AND A%(1)>1 THEN A%(1)=A%(1)-1
370 IF R%>6 AND A%(1)<12 THEN A%(1)=A%(1)+1
380 REM walls at car row
390 WA%=A%(L%)
400 REM keys — stop at walls
410 K$=INKEY$(0)
420 IF K$="Z" OR K$="z" THEN IF B%>WA%+1 THEN B%=B%-1
430 IF K$="Z" OR K$="z" THEN IF B%<=WA%+1 THEN H%=1
440 IF K$="X" OR K$="x" THEN IF B%<WA%+5 THEN B%=B%+1
450 IF K$="X" OR K$="x" THEN IF B%>=WA%+5 THEN H%=1
460 IF B%<=WA% THEN B%=WA%+1 : H%=1
470 IF B%>=WA%+6 THEN B%=WA%+5 : H%=1
480 REM wipe
490 FOR Y%=1 TO L%+3
500 PRINT TAB(0,Y%);BL$
510 NEXT
520 PRINT TAB(0,0);"Z / z = left     X / x = right"
530 REM draw road ahead (each row its own wall X)
540 FOR I%=1 TO L%-1
550 X%=A%(I%)
560 PRINT TAB(X%,I%);"*     *"
570 NEXT
580 REM car line
590 GOSUB 2000
600 IF H%=1 THEN C%=C%+1 : SOUND 1,-15,50,2
610 IF H%=1 THEN COLOUR 0,7
620 PRINT TAB(WA%,L%);R$
630 IF H%=1 THEN PRINT TAB(0,L%+2);"CRASH  crashes:";C%;"   stage:";G%;"   "
640 IF H%=0 THEN PRINT TAB(0,L%+2);"crashes:";C%;"   stage:";G%;"   "
650 COLOUR 7,0
660 G%=G%+1
670 IF H%=1 THEN WAIT 25 ELSE WAIT 10
680 IF C%<10 THEN 260

700 REM results
710 CLS
720 PRINT TAB(2,4);"YOU COMPLETED ";G%;" STAGES"
730 PRINT
740 IF G%<40 THEN PRINT " You need lessons.":GOTO 770
750 IF G%<100 THEN PRINT " Not bad for an amateur.":GOTO 770
760 PRINT " You are just the best!"
770 PRINT
780 PRINT " Play again? (Y/N)"
790 G$=GET$
800 IF G$="Y" OR G$="y" THEN 200
810 IF G$="N" OR G$="n" THEN 830
820 GOTO 790
830 CLS
840 PRINT "Thanks for playing ROADRACE."
850 END

2000 REM car line string (gap WA%+1..WA%+5)
2010 O%=B%-WA%
2020 IF O%=1 THEN R$="*O    *":RETURN
2030 IF O%=2 THEN R$="* O   *":RETURN
2040 IF O%=3 THEN R$="*  O  *":RETURN
2050 IF O%=4 THEN R$="*   O *":RETURN
2060 IF O%=5 THEN R$="*    O*":RETURN
2070 R$="*  O  *":RETURN

9000 PRINT:PRINT "Error ";ERR;" at ";ERL
9010 END
