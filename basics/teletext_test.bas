    10 MODE 7
    20 PRINT "MODE 7 Teletext Test"
    30 PRINT
    40 REM --- Colours (control codes take space) ---
    50 PRINT CHR$(129);"Red text"
    60 PRINT CHR$(130);"Green text"
    70 PRINT CHR$(131);"Yellow text"
    80 PRINT CHR$(132);"Blue text"
    90 PRINT CHR$(133);"Magenta text"
   100 PRINT CHR$(134);"Cyan text"
   110 PRINT CHR$(135);"White text (default)"
   120 PRINT
   130 REM --- Mosaic graphics ---
   140 PRINT "Mosaic test: "
   150 PRINT CHR$(145);CHR$(160+1);CHR$(145);CHR$(160+2);CHR$(145);CHR$(160+4)
   160 PRINT CHR$(145);CHR$(160+8);CHR$(145);CHR$(160+16);CHR$(145);CHR$(160+32)
   170 PRINT
   180 REM --- Control codes take space ---
   190 PRINT "Note: Control codes above took one character space each."
   200 PRINT "This is how real Teletext worked on the BBC Micro AND P2000."
   210 END
