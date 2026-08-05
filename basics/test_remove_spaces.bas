10 PRINT "Please input a string :"
20 INPUT A$
30 PROCremove_spaces(A$)
40 END
100 DEF PROCremove_spaces(A$)
110 LOCAL pos_space%
120 PRINT A$
130 pos_space%=INSTR(A$," "):REM =0 if no spaces
140 IF pos_space% THEN
150   A$=LEFT$(A$,pos_space%-1)+RIGHT$(A$,pos_space%+1)
160   PROCremove_spaces(A$)
170 ENDIF
180 ENDPROC
