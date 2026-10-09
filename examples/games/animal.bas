REM mini_basic: UTF-8 listing (was Russell tokenized .bbc; binary corrupted by
REM length-breaking @% patch 2026-07-26). Source of truth also in
REM test/corpus/bbcsdl/games/animal.txt. @%=0 avoids STR$ pad / N? tree bug.
:
      ON ERROR IF ERR=17 CHAIN @lib$+"../examples/tools/touchide" ELSE MODE 3 : PRINT REPORT$ : END
      
      REM @% width 0: STR$ must not pad tree indices (was &90A → corrupt \"N?\" nodes)
      CLS:@%=0:WIDTH 0:PRINT TAB(15)"ANIMAL"
      PRINT "Creative Computing Morristown New Jersey"''
      REM by Nathan Teichholtz & Steve North
      REM from an original idea by Arthur Luehrmann.
      REM Modified by Chris Atkinson and Richard Russell.
      :
      REMM ON ERROR IF ERR=17 THEN PROCexit ELSE PRINT:REPORT:PRINT" at line ";ERL:END
      MAX=(HIMEM-LOMEM)/40
      DIM A$(MAX)
      PRINT "Play 'Guess the Animal'"
      :
      X=OPENIN(@usr$+"animal.dat")
      IF X=0 X=OPENIN(@dir$+"animal.dat")
      IF X<>0 PROCread
      IF A$(0)="" OR LEFT$(A$(1),2)<>"\Q" THEN FOR I=0 TO 3:READ A$(I):NEXT I
      :
      REM ***
      REM MAIN CONTROL SECTION
      REM ***
      REPEAT
        IF FNquery("Are you thinking of an animal ")="N" THEN PROCexit
        K=1
        REPEAT
          PROCquestion
        UNTIL LEFT$(A$(K),2)<>"\Q"
        A$=FNquery("Is it "+FNart(MID$(A$(K),3)))
        IF A$="Y" THEN PRINT "Why not try another one?"'' ELSE PROCnew
      UNTIL FALSE
      ;
      REM ***
      REM NEW ANIMAL
      REM ***
      DEF PROCnew
      PRINT ''
      PRINT "Sorry, I guessed ";FNart(MID$(A$(K),3));"."
      INPUT "What animal were you thinking of? ",V$
      V$=FNstrip(FNconvlc(V$))
      PRINT "What question distinguishes "+FNart(V$)+" from "+FNart(MID$(A$(K),3))+"?"
      INPUT "Type your question: ",X$
      X$=FNcapital(X$)
      IF RIGHT$(X$,1)="?" THEN X$=LEFT$(X$,LEN(X$)-1)
      A$=FNquery("For "+FNart(V$)+" the answer would be ")
      IF A$="Y" THEN B$="N"
      IF A$="N" THEN B$="Y"
      Z1=VAL(A$(0))
      A$(0)=STR$(Z1+2)
      A$(Z1)=A$(K)
      A$(Z1+1)="\A"+V$
      A$(K)="\Q"+X$+"\"+A$+STR$(Z1+1)+"\"+B$+STR$(Z1)+"\"
      ENDPROC
      ;
      REM ***
      REM PRINT QUESTIONS
      REM ***
      DEF PROCquestion
      Q$=A$(K)
      REM Only walk question nodes (\Q...); animal leaves (\A...) are handled by the main loop.
      IF LEFT$(Q$,2)<>"\Q" THEN ENDPROC
      C$=FNquery(MID$(Q$,3,INSTR(Q$,"\",3)-3))
      REM Branch tags in the tree are uppercase \Y / \N (INSTR is case-sensitive).
      IF C$="y" THEN C$="Y"
      IF C$="n" THEN C$="N"
      T$="\"+C$
      X=INSTR(Q$,T$,3)
      IF X=0 THEN ENDPROC
      Y=INSTR(Q$,"\",X+1)
      IF Y=0 THEN ENDPROC
      K=VAL(MID$(Q$,X+2,Y-X-2))
      ENDPROC
      ;
      REM ***
      REM READ DATA FILE
      REM ***
      DEF PROCread
      PRINT "Just let me refresh my memory"
      Z=0
      REPEAT INPUT #X,A$(Z):Z=Z+1
      UNTIL EOF#X OR Z=MAX+1 OR A$(Z-1)=""
      CLOSE #X
      ENDPROC
      ;
      REM ***
      REM PRINT NAME OF ANIMAL
      REM ***
      DEF PROCprint
      PRINT TAB(10*X);MID$(A$(I),3);
      X=(X+1) MOD 4
      ENDPROC
      ;
      REM ***
      REM LIST CONTENTS
      REM ***
      DEF PROCexit
      REM ON ERROR OFF
      PRINT "Animals I already know are:"
      X=0:I=0
      REPEAT I=I+1
        IF LEFT$(A$(I),2)="\A" THEN PROCprint
      UNTIL A$(I)="" OR I=MAX
      PRINT "Room for ";INT((MAX-I)/3);" more."
      :
      IF FNquery("Do you want to save these on disk")="Y" THEN
        REM ***
        REM DUMP FILE IF REQUESTED
        REM ***
        X=OPENOUT(@usr$+"animal.dat"):Z=0
        REPEAT PRINT# X,A$(Z):Z=Z+1
        UNTIL A$(Z)="" OR Z=MAX+1
        CLOSE #X
        PRINT "Animal data saved."
      ENDIF
      PRINT "Close the game window to exit."
      REPEAT WAIT 1 : UNTIL FALSE
      ENDPROC
      ;
      DATA 4,\QDoes it fly\N2\Y3\,\Agoldfish,\Asparrow,
      ;
      REM. NOW THE FUNCTIONS
      ;
      DEF FNart(noun$):REM Indefinite article appender
      IF INSTR("AEIOUaeiou",LEFT$(noun$,1)) THEN ="an "+noun$ ELSE ="a "+noun$
      ;
      DEF FNstrip(name$):REM Article stripper
      name$=FNnospace(name$)
      LOCAL AT$,Z
      RESTORE +1
      REPEAT Z=Z+1:READ AT$
      UNTIL AT$=LEFT$(name$,LEN(AT$)) OR Z=10
      IF Z<10 THEN name$=MID$(name$,1+LEN(AT$))
      =FNnospace(name$)
      DATA A ,AN ,THE ,a ,an ,the ,An ,The ,THe ,,
      ;
      DEF FNnospace(name$)
      name$=" "+name$
      REPEAT name$=MID$(name$,2)
      UNTIL LEFT$(name$,1)<>" "
      =name$
      ;
      DEF FNconvlc(name$)
      LOCAL L%,A%,B$
      FOR L%=1 TO LEN(name$)
        A%=ASC(MID$(name$,L%))
        IF A%<97 AND A%>64 THEN A%=A%+32
        B$=B$+CHR$(A%):NEXT L%
      =B$
      ;
      DEF FNcapital(name$)
      LOCAL A$
      name$=FNnospace(FNconvlc(name$))
      IF ASC(name$)<97 THEN =name$
      A$=CHR$(ASC(name$)-32)
      A$=A$+MID$(name$,2)
      =A$
      ;
      DEF FNquery(prompt$)
      LOCAL A$
      IF prompt$="" THEN prompt$="(Y/N) "
      IF INSTR(prompt$,"(Y/N)")=0 AND RIGHT$(prompt$,1)<>"?" THEN prompt$=prompt$+" (Y/N)"
      REPEAT
        REM Newline before each ask so a bare "?" is never the only visible cue.
        PRINT
        PRINT prompt$;:INPUT A$
        A$=LEFT$(FNcapital(A$),1)
        IF A$="y" THEN A$="Y"
        IF A$="n" THEN A$="N"
      UNTIL A$="Y" OR A$="N"
      =A$
