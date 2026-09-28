      REM "Surks" (mini_basic-compatible fork)
      REM by David Williams
      REM Version 1.01 (20-Feb-2019)
      REM
      REM Adapted for mini_basic 2026-09-26: two constructs the original
      REM BB4W source uses are not (yet) supported here. Every change is
      REM marked with a "MINI_BASIC:" comment right where it happens;
      REM everything else is unchanged from examples/graphics/surks.bbc.

      ON ERROR PROCError( REPORT$ + " at line " + STR$ERL )

      BB4W% = (INKEY(-256) == &57)

      ScrW% = 640

      IF BB4W% THEN
        ScrH% = 512
      ELSE
        DIM mode{ fmt%, w%, h%, r%, d% }
        SYS "SDL_GetCurrentDisplayMode", 0, mode{}
        IF mode.h% > mode.w% THEN
          ScrH% = (INT(mode.h%/mode.w% * ScrW%) + 1) AND -2
        ELSE
          ScrH% = 512
        ENDIF
      ENDIF

      VDU 23, 22, ScrW%; ScrH%; 8, 16, 16, 0 : OFF
      VDU 24, 0; 0; ScrW%*2-2; ScrH%*2-2;

      MaxCircles% = 1000
      MaxThickness% = 16
      MinRadius% = MaxThickness%/2
      MaxRadius% = 1/4 * SQR(ScrW%^2 + ScrH%^2)
      MaxTries% = 10000

      REM MINI_BASIC: the original DIMs an array of structs,
      REM   DIM circle{(MaxCircles%-1) x%, y%, r%, t%}
      REM and reads fields back with circle{(I%)}.r% etc. mini_basic can
      REM assign circle{(0)}.x% = ... without error, but cannot yet read a
      REM struct-array element's member back (indexed struct-array reads
      REM are unimplemented — see docs/LANGUAGE_FEATURES_1.00.md and PR #17's
      REM thread). Four parallel arrays stand in for the one struct array.
      DIM cx%(MaxCircles%-1), cy%(MaxCircles%-1), cr%(MaxCircles%-1), ct%(MaxCircles%-1)

      R% = RND(-TIME)

      REPEAT

        nCircs% = 0
        finished% = FALSE

        REM Set background colour:
        PROCGetRandomRGB( r&, g&, b& )
        COLOR 1, r&/4, g&/4, b&/4
        GCOL 0, 128+1
        CLG

        REPEAT

          REM Get random coordinates and radius for new circle such that
          REM it doesn't overlap with any previously defined circles:
          IF nCircs% = 0 THEN
            PROCGetRandomCircle( x%, y%, r%, t% )
          ELSE
            tries% = 0
            REPEAT
              valid% = TRUE
              PROCGetRandomCircle( x%, y%, r%, t% )
              REM MINI_BASIC: original loop used "EXIT FOR" to stop early
              REM once valid%=FALSE. mini_basic's --dialect bbc rejects
              REM EXIT FOR/WHILE/REPEAT by design (it's a mini/SDL
              REM extension, not real BBC BASIC), so guard the body with
              REM IF valid% instead — same result, just no early exit.
              FOR I% = 0 TO nCircs%
                IF valid% THEN
                  R% = (r% + cr%(I%) + t%)^2
                  IF (x%-cx%(I%))^2 + (y%-cy%(I%))^2 < R% THEN
                    valid% = FALSE
                  ENDIF
                ENDIF
              NEXT I%
              tries% += 1
              IF tries% = MaxTries% THEN finished% = TRUE
            UNTIL valid% OR finished%
          ENDIF

          REM Draw the circle:
          IF NOT finished% THEN

            REM MINI_BASIC: parallel arrays instead of circle{(nCircs%)}.x% etc.
            cx%(nCircs%) = x%
            cy%(nCircs%) = y%
            cr%(nCircs%) = r%
            ct%(nCircs%) = t%

            IF RND(30)=1 OR nCircs%=0 THEN
              gfxPlotMode% = 2 + RND(2)
              PROCGetRandomRGB( r&, g&, b& )
            ENDIF

            REM Fill colour RGB is from scaled r&, g& and b&:
            f = 0.5 + 1.5*RND(1) : REM scale factor (f) in the range 0.5 to 2.0
            REM Scale RGB values and clip them to 255:
            r2% = f * r& : IF r2% > 255 THEN r2% = 255
            g2% = f * g& : IF g2% > 255 THEN g2% = 255
            b2% = f * b& : IF b2% > 255 THEN b2% = 255

            REM Draw filled circle:
            COLOR 1, r2%, g2%, b2% : GCOL 0,1
            CIRCLE FILL 2*x%, 2*y%, 2*r%

            REM Draw thick outline:
            COLOR 1, 255-r&, 255-g&, 255-b&
            VDU 23, 23, t%| : REM Set line/outline thickness
            CIRCLE 2*x%, 2*y%, 2*(r%+1)

            REM Draw ellipses for grid effect:
            GCOL gfxPlotMode%, 1
            t2% = (0.75 + 0.25*RND(1)) * t% : REM random-ish thickness
            VDU 23, 23, t2%|
            S% = 4 + RND(6)*t%
            FOR I% = r% TO 1 STEP -S%
              ELLIPSE 2*x%, 2*y%, 2*r%, 2*I%
              ELLIPSE 2*x%, 2*y%, 2*I%, 2*r%
            NEXT I%
            VDU 23, 23, 1| : REM Restore line/outline thickness to 1 pixel's width

            nCircs% += 1

          ENDIF

        UNTIL (nCircs% = MaxCircles%) OR finished%

        t0% = TIME + 250
        REPEAT WAIT 4 : UNTIL TIME >= t0%

      UNTIL FALSE : REM Repeat ad infinitum
      END
      :
      :
      :
      :
      DEF PROCGetRandomCircle( RETURN x%, RETURN y%, RETURN r%, RETURN t% )
      x% = RND(ScrW%)-1
      y% = RND(ScrH%)-1
      r% = MinRadius% + RND(MaxRadius%-MinRadius%)
      t% = MaxThickness% * r%/MaxRadius% + 1
      ENDPROC
      :
      :
      :
      :
      DEF PROCGetRandomRGB( RETURN r&, RETURN g&, RETURN b& )
      LOCAL C%
      CASE RND(15) OF
        WHEN  1: C% = &FF0000
        WHEN  2: C% = &00FF00
        WHEN  3: C% = &0000FF
        WHEN  4: C% = &FFFF00
        WHEN  5: C% = &FF00FF
        WHEN  6: C% = &00FFFF
        WHEN  7: C% = &FF8000
        WHEN  8: C% = &FF0080
        WHEN  9: C% = &00FF80
        WHEN 10: C% = &80FF00
        WHEN 11: C% = &0080FF
        WHEN 12: C% = &8000FF
        WHEN 13: C% = &FF8080
        WHEN 14: C% = &80FF80
        WHEN 15: C% = &8080FF
      ENDCASE
      r& = C% >> 16
      g& = C% >> 8
      b& = C%
      ENDPROC
      :
      :
      :
      :
      DEF PROCError( s$ )
      IF NOT BB4W% THEN
        IF ERR=17 CHAIN @lib$+"../examples/tools/touchide"
      ENDIF
      CLS : ON : VDU 7
      PRINT '" "+s$;
      REPEAT
        WAIT 10
      UNTIL FALSE
      ENDPROC
