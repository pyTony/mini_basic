REM ============================================================
REM  MODE 7 teletext test screen (SAA5050 subset + future rows)
REM ============================================================
REM  Run (pygame recommended so mosaics render):
REM    python -m mini_basic --dialect bbc --display pygame examples/teletext/mode7_test_screen.bas
REM
REM  IMPLEMENTED today (should look correct):
REM    129-135 alpha colours   145-151 graphics colours
REM    136/137 flash           154/155 separated mosaics
REM    156/157 black / new bg  158/159 hold graphics
REM    mosaic chars 160-191 / 224-255 (2x3 sextants)
REM
REM  FUTURE (rows marked [F] — may be wrong until full SAA5050):
REM    140/141 double height   152/153 conceal / cont graphics
REM    158/159 already partial hold; boxed, contiguous, etc.
REM ============================================================

MODE 7
CLS
OFF

REM --- Title (white alpha by default after CLS) ---
PRINT CHR$141;CHR$135;" TELETEXT MODE 7 TEST SCREEN"
PRINT CHR$141;CHR$135;" TELETEXT MODE 7 TEST SCREEN"
PRINT CHR$135;" mini_basic — implemented + [F]uture rows"
PRINT

REM --- Alpha colours 129-135 ---
PRINT CHR$135;"1 ALPHA FG 129-135"
PRINT CHR$129;" RED";CHR$130;" GREEN";CHR$131;" YELLOW";CHR$132;" BLUE";
PRINT CHR$133;" MAGENTA";CHR$134;" CYAN";CHR$135;" WHITE"
PRINT

REM --- Graphics colours + sample mosaics ---
PRINT CHR$135;"2 GRAPHICS 145-151 + mosaic (e.g. CHR$185)"
PRINT CHR$145;CHR$185;CHR$185;CHR$185;" ";
PRINT CHR$146;CHR$185;CHR$185;CHR$185;" ";
PRINT CHR$147;CHR$185;CHR$185;CHR$185;" ";
PRINT CHR$148;CHR$185;CHR$185;CHR$185;" ";
PRINT CHR$149;CHR$185;CHR$185;CHR$185;" ";
PRINT CHR$150;CHR$185;CHR$185;CHR$185;" ";
PRINT CHR$151;CHR$185;CHR$185;CHR$185
PRINT

REM --- Separated mosaics ---
PRINT CHR$135;"3 SEPARATED 154 / CONTIGUOUS 155"
PRINT CHR$145;CHR$154;CHR$185;CHR$185;CHR$185;" sep ";
PRINT CHR$155;CHR$185;CHR$185;CHR$185;" cont"
PRINT

REM --- Background ---
PRINT CHR$135;"4 BACKGROUND 156 black / 157 new"
PRINT CHR$131;CHR$157;" YELLOW BG ";CHR$156;" black bg again"
PRINT

REM --- Flash ---
PRINT CHR$135;"5 FLASH 136 / STEADY 137"
PRINT CHR$136;CHR$129;" FLASHING RED ";CHR$137;CHR$130;" steady green"
PRINT

REM --- Hold graphics (partial) ---
PRINT CHR$135;"6 HOLD GRAPHICS 158/159 (partial)"
PRINT CHR$145;CHR$185;CHR$158;CHR$129;"alpha";CHR$185;" ";CHR$159;" end hold"
PRINT

REM --- Mosaic strip ---
PRINT CHR$135;"7 MOSAIC STRIP 160..175 (graphics white)"
PRINT CHR$151;
FOR C%=160 TO 175
  PRINT CHR$C%;
NEXT
PRINT
PRINT

REM ========== FUTURE / incomplete rows ==========
PRINT CHR$131;"--- [F] FUTURE SAA5050 (expect wrong until done) ---"
PRINT CHR$135;"[F] DOUBLE HEIGHT 141 (two lines should be tall chars)"
PRINT CHR$141;CHR$130;" DOUBLE HEIGHT GREEN"
PRINT CHR$141;CHR$130;" DOUBLE HEIGHT GREEN"
PRINT CHR$135;"[F] CONCEAL 152 then reveal (should hide then show)"
PRINT CHR$152;CHR$129;"CONCEALED TEXT";CHR$153;" revealed? (if 153 used)"
PRINT
PRINT CHR$135;"ESC / Ctrl+C to exit  |  WAIT holds the page"
WAIT 600
END
