10 REM ROADRACE - road scrolls DOWN toward car; walls snake L/R
20 REM Z/z left, X/x right. 10 crashes ends.

100 ON ERROR GOTO 9000
110 MODE 0
120 W%=40 : L%=8
130 GOSUB 1000
140 GOTO 200

1000 CLS
1010 PRINT TAB(5,2);"ROADRACE"
1020 PRINT TAB(3,4);"Keep O between the * walls"
1030 PRINT
1040 PRINT "  Z/z left, X/x right — road scrolls down."
1050 PRINT "  10 crashes ends the run."
1060 PRINT
1070 PRINT "  Press any key to start..."
1080 G$=GET$
1090 RETURN

200 CLS
210 DIM A%(L%)
220 FOR I%=1 TO L% : A%(I%)=8 : NEXT
230 B%=A%(L%)+3 : C%=0 : G%=0
240 BL$=STRING$(W%," ")

260 H%=0
270 FOR I%=L% TO 2 STEP -1
280 J%=I%-1
290 A%(I%)=A%(J%)
300 NEXT
310 N%=10 : R%=RND(N%)
320 A%(1)=A%(2)
330 IF R%<4 AND A%(1)>1 THEN A%(1)=A%(1)-1
340 IF R%>6 AND A%(1)<12 THEN A%(1)=A%(1)+1
350 WA%=A%(L%)
360 K$=INKEY$(0)
370 IF K$="Z" OR K$="z" THEN IF B%>WA%+1 THEN B%=B%-1
380 IF K$="Z" OR K$="z" THEN IF B%<=WA%+1 THEN H%=1
390 IF K$="X" OR K$="x" THEN IF B%<WA%+5 THEN B%=B%+1
400 IF K$="X" OR K$="x" THEN IF B%>=WA%+5 THEN H%=1
410 IF B%<=WA% THEN B%=WA%+1 : H%=1
420 IF B%>=WA%+6 THEN B%=WA%+5 : H%=1
430 FOR Y%=1 TO L%+3
440 PRINT TAB(0,Y%);BL$
450 NEXT
460 PRINT TAB(0,0);"Z / z = left     X / x = right"
470 FOR I%=1 TO L%-1
480 X%=A%(I%)
490 PRINT TAB(X%,I%);"*     *"
500 NEXT
510 GOSUB 2000
520 IF H%=1 THEN C%=C%+1 : SOUND 1,-15,50,2
530 IF H%=1 THEN COLOUR 0,7
540 PRINT TAB(WA%,L%);R$
550 IF H%=1 THEN PRINT TAB(0,L%+2);"CRASH  crashes:";C%;"   stage:";G%;"   "
560 IF H%=0 THEN PRINT TAB(0,L%+2);"crashes:";C%;"   stage:";G%;"   "
570 COLOUR 7,0
580 G%=G%+1
590 IF H%=1 THEN WAIT 25 ELSE WAIT 10
600 IF C%<10 THEN 260

700 CLS
710 PRINT TAB(2,4);"YOU COMPLETED ";G%;" STAGES"
720 PRINT
730 IF G%<40 THEN PRINT " You need lessons.":GOTO 760
740 IF G%<100 THEN PRINT " Not bad for an amateur.":GOTO 760
750 PRINT " You are just the best!"
760 PRINT
770 PRINT " Play again? (Y/N)"
780 G$=GET$
790 IF G$="Y" OR G$="y" THEN 200
800 IF G$="N" OR G$="n" THEN 820
810 GOTO 780
820 CLS
830 PRINT "Thanks for playing ROADRACE."
840 END

2000 O%=B%-WA%
2010 IF O%=1 THEN R$="*O    *":RETURN
2020 IF O%=2 THEN R$="* O   *":RETURN
2030 IF O%=3 THEN R$="*  O  *":RETURN
2040 IF O%=4 THEN R$="*   O *":RETURN
2050 IF O%=5 THEN R$="*    O*":RETURN
2060 R$="*  O  *":RETURN

9000 PRINT:PRINT "Error ";ERR;" at ";ERL
9010 END
