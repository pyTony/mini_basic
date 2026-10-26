Manual / scratch scripts — not run by unittest discover.

user_prog_scratch.py      Ad-hoc PRINT loop timing experiment
bbcsdl_jump_checks.bas    14 interactive GOTO/GOSUB/ON jump-into/out-of-block
                          checks (FOR/WHILE/IF/CASE/REPEAT local jumps, ON
                          GOTO/GOSUB, a missing-target check); menu loops in
                          a REPEAT so you can run several tests per session
                          (0 quits, an out-of-range choice redisplays the
                          menu), record results against real BBCSDL. Self-
                          describing (REM dialect: bbc), so it also opens as
                          bbc in the editor with no dialect selection needed.
                          Launch: python -m mini_basic
                          test/manual/bbcsdl_jump_checks.bas