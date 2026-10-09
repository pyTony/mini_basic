import io
from mini_basic import BASICInterpreter, InterpreterConfig

interp = BASICInterpreter(InterpreterConfig(dialect='mini'))
lines = [
    (10, 'PRINT "Please input a string :"'),
    (20, 'INPUT A$'),
    (30, 'PROCremove_spaces(A$)'),
    (40, 'END'),
    (100, 'DEF PROCremove_spaces(A$)'),
    (110, 'LOCAL pos_space%'),
    (120, 'PRINT A$'),
    (130, 'pos_space%=INSTR(A$," ")'),
    (140, 'IF pos_space% THEN'),
    (150, '  A$=LEFT$(A$,pos_space%-1)+MID$(A$,pos_space%+1)'),
    (160, '  PROCremove_spaces(A$)'),
    (170, 'ENDIF'),
    (180, 'ENDPROC'),
]
for ln, st in lines:
    interp.program[ln] = st
line_nums = sorted(interp.program.keys())
print('endproc', interp._find_matching_endproc(100, line_nums))
procs, _ = interp._scan_user_procedures(line_nums)
print('scan procs', procs)
interp._build_user_procedures()
print('build procs', interp.user_procedures)
interp.str_variables['A'] = 'A quick brown fox'
buf = io.StringIO()
interp._program_stdout = buf
proc = interp.user_procedures['remove_spaces']
interp._call_procedure(proc, ['A$'])
print('output:', repr(buf.getvalue()))
print('cmd LOCAL:', interp._parse_command('LOCAL pos_space%'))