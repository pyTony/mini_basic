1 REM dialect: mini
2 REM READABLE VERSION of superstartrek.bas (MITS 8K): same line numbers, descriptive
3 REM names, labels instead of numeric jumps. Runs as mini, not MITS: the MITS number
4 REM spacing and "?" after INPUT prompts are written out. Glossary: lines 271-329.
5 CLEAR 1000
10 restartGame: REM SUPER STARTREK - MAY 16,1978 - REQUIRES 24K MEMORY
30 REM
40 REM ****        **** STAR TREK ****        ****
50 REM **** SIMULATION OF A MISSION OF THE STARSHIP ENTERPRISE,
60 REM **** AS SEEN ON THE STAR TREK TV SHOW.
70 REM **** ORIGIONAL PROGRAM BY MIKE MAYFIELD, MODIFIED VERSION
80 REM **** PUBLISHED IN DEC'S "101 BASIC GAMES", BY DAVE AHL.
90 REM **** MODIFICATIONS TO THE LATTER (PLUS DEBUGGING) BY BOB
100 REM *** LEEDOM - APRIL & DECEMBER 1974,
110 REM *** WITH A LITTLE HELP FROM HIS FRIENDS . . .
120 REM *** COMMENTS, EPITHETS, AND SUGGESTIONS SOLICITED --
130 REM *** SEND TO:  R. C. LEEDOM
140 REM ***           WESTINGHOUSE DEFENSE & ELECTRONICS SYSTEMS CNTR.
150 REM ***           BOX 746, M.S. 338
160 REM ***           BALTIMORE, MD  21203
170 REM ***
180 REM *** CONVERTED TO MICROSOFT 8 K BASIC 3/16/78 BY JOHN GORDERS
190 REM *** LINE NUMBERS FROM VERSION STREK7 OF 1/12/75 PRESERVED AS
200 REM *** MUCH AS POSSIBLE WHILE USING MULTIPLE STATEMENTS PER LINE
205 REM *** SOME LINES ARE LONGER THAN 72 CHARACTERS; THIS WAS DONE
210 REM *** BY USING "?" INSTEAD OF "PRINT" WHEN ENTERING LINES
215 REM ***
220 PRINT:PRINT:PRINT:PRINT:PRINT:PRINT:PRINT:PRINT:PRINT:PRINT:PRINT
221 PRINT"                                    ,------*------,"
222 PRINT"                    ,-------------   '---  ------'"
223 PRINT"                     '-------- --'      / /"
224 PRINT"                         ,---' '-------/ /--,"
225 PRINT"                          '----------------'":PRINT
226 PRINT"                    THE USS ENTERPRISE --- NCC-1701"
227 PRINT:PRINT:PRINT:PRINT:PRINT
260 REM CLEAR 600
270 spaces$="                         "
271 REM GAME STATE
272 REM  stardate / startStardate / missionDays  current date, date mission began, days allowed
273 REM  energy / energyAtStart / shields          ship energy, full energy, energy put into shields
274 REM  torpedoes / torpedoesAtStart              photon torpedoes left / at full supply
275 REM  docked                                    1 while next to a starbase (no Klingon fire)
276 REM  klingonsLeft / klingonsAtStart            Klingons still alive / at the start (galaxy total)
277 REM  starbasesLeft                             starbases still in the galaxy
278 REM  klingonStartEnergy                        about 200: base energy of a new Klingon ship
279 REM  plural$ / isAre$                          "S" and " ARE " for "STARBASE(S) ... IS/ARE"
280 REM  maxWarp$                                 "8" or "0.2" shown in the warp factor prompt (original X$)
281 REM POSITION
282 REM  quadrantX/Y   sectorX/Y                  Enterprise quadrant (1-8) and sector (1-8)
283 REM  oldQuadrantX/Y                            quadrant before a move (to detect a change)
284 REM  klingonsHere / starbasesHere / starsHere  contents of the current quadrant
285 REM  starbaseX/Y                               sector of the starbase in this quadrant
286 REM  galaxy(x,y)         klingons*100 + starbases*10 + stars for each quadrant
287 REM  chartedGalaxy(x,y)  the same, but only for quadrants the ship has scanned
288 REM  klingon(n,1..3)     sector X, sector Y and energy of Klingon n in this quadrant
289 REM  deviceDamage(1..8)  negative = damaged: warp, short range, long range, phasers,
290 REM                      photon tubes, damage control, shield control, computer
291 REM  courseVector(1..9,1..2)  X/Y step for each of the 8 compass courses (1 and 9 equal)
292 REM  quadrantMap$        192 characters: 8x8 sectors of 3 characters each ("<*>", "+K+", ">!<", " * ")
293 REM  commandNames$       the 9 three-letter commands in order: NAV SRS LRS PHA TOR SHE DAM COM XXX
294 REM  condition$ / borderLine$ / spaces$   GREEN/YELLOW/*RED*/DOCKED, a dash line, 25 blanks
295 REM  placeName$          result of the name lookups: quadrant name or device name
296 REM REUSED VARIABLES (the original uses one name for several jobs; this listing uses
297 REM one name per job, chosen by line range)
298 REM  index variables     klingonIndex, deviceIndex, commandIndex, stepIndex, displayRow ... = original I, J, L
299 REM  randomX/Y           random sector (original R1, R2); deviceNumber = original R1 as a device
300 REM  sectorSymbol$       3-character map symbol (original A$); commandText$ / answer$ = typed text
301 REM  X and Y             galacticX/Y while moving, torpedoX/Y for a torpedo, phaserUnits and
302 REM                      shieldUnits for the typed number
303 REM  8100-8500           computer direction calculator reuses A, X, C1, W1: deltaX, deltaY,
304 REM                      directionBase, toX (fromX/fromY are loaded into directionBase and deltaX first)
305 REM  computerMode        1 = numbers / return to command after one report, 0 = galaxy map or all Klingons
306 REM HELPERS
307 REM  FNdistance(0)       distance from the Enterprise to Klingon klingonIndex
308 REM  FNrandomSector(1)   random whole number 1 to 8
330 DIM galaxy(8,8),courseVector(9,2),klingon(3,3),scanCell(3),chartedGalaxy(8,8),deviceDamage(8)
370 stardate=INT(RND(1)*20+20)*100:startStardate=stardate:missionDays=25+INT(RND(1)*10):docked=0:energy=3000:energyAtStart=energy
440 torpedoes=10:torpedoesAtStart=torpedoes:klingonStartEnergy=200:shields=0:starbasesLeft=2:klingonsLeft=0:plural$="":isAre$=" IS "
470 DEF FNdistance(unusedArgument)=SQR((klingon(klingonIndex,1)-sectorX)^2+(klingon(klingonIndex,2)-sectorY)^2)
475 DEF FNrandomSector(rndArgument)=INT(RND(rndArgument)*7.98+1.01)
480 REM INITIALIZE ENTERPRIZE'S POSITION
490 quadrantX=FNrandomSector(1):quadrantY=FNrandomSector(1):sectorX=FNrandomSector(1):sectorY=FNrandomSector(1)
530 FOR courseIndex=1 TO 9:courseVector(courseIndex,1)=0:courseVector(courseIndex,2)=0:NEXT courseIndex
540 courseVector(3,1)=-1:courseVector(2,1)=-1:courseVector(4,1)=-1:courseVector(4,2)=-1:courseVector(5,2)=-1:courseVector(6,2)=-1
600 courseVector(1,2)=1:courseVector(2,2)=1:courseVector(6,1)=1:courseVector(7,1)=1:courseVector(8,1)=1:courseVector(8,2)=1:courseVector(9,2)=1
670 FOR deviceIndex=1 TO 8:deviceDamage(deviceIndex)=0:NEXT deviceIndex
710 commandNames$="NAVSRSLRSPHATORSHEDAMCOMXXX"
810 REM SETUP WHAT EXHISTS IN GALAXY . . .
815 REM K3= # KLINGONS  B3= # STARBASES  S3 = # STARS
820 FOR galaxyX=1 TO 8:FOR galaxyY=1 TO 8:klingonsHere=0:chartedGalaxy(galaxyX,galaxyY)=0:randomChance=RND(1)
850 IF randomChance>.98 THEN klingonsHere=3:klingonsLeft=klingonsLeft+3:GOTO placeGalaxyStarbase
860 IF randomChance>.95 THEN klingonsHere=2:klingonsLeft=klingonsLeft+2:GOTO placeGalaxyStarbase
870 IF randomChance>.80 THEN klingonsHere=1:klingonsLeft=klingonsLeft+1
980 placeGalaxyStarbase: starbasesHere=0:IF RND(1)>.96 THEN starbasesHere=1:starbasesLeft=starbasesLeft+1
1040 galaxy(galaxyX,galaxyY)=klingonsHere*100+starbasesHere*10+FNrandomSector(1):NEXT galaxyY:NEXT galaxyX:IF klingonsLeft>missionDays THEN missionDays=klingonsLeft+1
1100 IF starbasesLeft<>0 THEN announceMission
1150 IF galaxy(quadrantX,quadrantY)<200 THEN galaxy(quadrantX,quadrantY)=galaxy(quadrantX,quadrantY)+120:klingonsLeft=klingonsLeft+1
1160 starbasesLeft=1:galaxy(quadrantX,quadrantY)=galaxy(quadrantX,quadrantY)+10:quadrantX=FNrandomSector(1):quadrantY=FNrandomSector(1)
1200 announceMission: klingonsAtStart=klingonsLeft:IF starbasesLeft<>1 THEN plural$="S":isAre$=" ARE "
1230 PRINT"YOUR ORDERS ARE AS FOLLOWS:"
1240 PRINT"     DESTROY THE";" ";klingonsLeft;" ";"KLINGON WARSHIPS WHICH HAVE INVADED"
1252 PRINT"   THE GALAXY BEFORE THEY CAN ATTACK FEDERATION HEADQUARTERS"
1260 PRINT"   ON STARDATE";" ";startStardate+missionDays;" ";"  THIS GIVES YOU";" ";missionDays;" ";"DAYS.  THERE";isAre$
1272 PRINT"  ";" ";starbasesLeft;" ";"STARBASE";plural$;" IN THE GALAXY FOR RESUPPLYING YOUR SHIP"
1280 PRINT:REM PRINT"HIT ANY KEY EXCEPT RETURN WHEN READY TO ACCEPT COMMAND"
1300 index=RND(1):REM IF INP(1)=13 THEN 1300
1310 REM HERE ANY TIME NEW QUADRANT ENTERED
1320 enterQuadrant: nameQuadrantX=quadrantX:nameQuadrantY=quadrantY:klingonsHere=0:starbasesHere=0:starsHere=0:regionNameOnly=0:repairBonus=.5*RND(1):chartedGalaxy(quadrantX,quadrantY)=galaxy(quadrantX,quadrantY)
1390 IF quadrantX<1 OR quadrantX>8 OR quadrantY<1 OR quadrantY>8 THEN resetQuadrantMap
1430 GOSUB quadrantNameLookup:PRINT:IF startStardate<>stardate THEN announceNewQuadrant
1460 PRINT"YOUR MISSION BEGINS WITH YOUR STARSHIP LOCATED"
1470 PRINT"IN THE GALACTIC QUADRANT, '";placeName$;"'.":GOTO readQuadrantContents
1490 announceNewQuadrant: PRINT"NOW ENTERING ";placeName$;" QUADRANT . . ."
1500 readQuadrantContents: PRINT:klingonsHere=INT(galaxy(quadrantX,quadrantY)*.01):starbasesHere=INT(galaxy(quadrantX,quadrantY)*.1)-10*klingonsHere
1540 starsHere=galaxy(quadrantX,quadrantY)-100*klingonsHere-10*starbasesHere:IF klingonsHere=0 THEN clearKlingonTable
1560 PRINT"COMBAT AREA      CONDITION RED":IF shields>200 THEN clearKlingonTable
1580 PRINT"   SHIELDS DANGEROUSLY LOW"
1590 clearKlingonTable: FOR klingonIndex=1 TO 3:klingon(klingonIndex,1)=0:klingon(klingonIndex,2)=0:NEXT klingonIndex
1600 resetQuadrantMap: FOR klingonIndex=1 TO 3:klingon(klingonIndex,3)=0:NEXT klingonIndex:quadrantMap$=spaces$+spaces$+spaces$+spaces$+spaces$+spaces$+spaces$+LEFT$(spaces$,17)
1660 REM POSITION ENTERPRISE IN QUADRANT, THEN PLACE "K3" KLINGONS, &
1670 REM "B3" STARBASES, & "S3" STARS ELSEWHERE.
1680 sectorSymbol$="<*>":placeX=sectorX:placeY=sectorY:GOSUB insertInQuadrantMap:IF klingonsHere<1 THEN placeQuadrantStarbase
1720 FOR klingonIndex=1 TO klingonsHere:GOSUB findEmptySector:sectorSymbol$="+K+":placeX=randomX:placeY=randomY
1780 GOSUB insertInQuadrantMap:klingon(klingonIndex,1)=randomX:klingon(klingonIndex,2)=randomY:klingon(klingonIndex,3)=klingonStartEnergy*(0.5+RND(1)):NEXT klingonIndex
1820 placeQuadrantStarbase: IF starbasesHere<1 THEN placeStars
1880 GOSUB findEmptySector:sectorSymbol$=">!<":placeX=randomX:starbaseX=randomX:placeY=randomY:starbaseY=randomY:GOSUB insertInQuadrantMap
1910 placeStars: FOR starIndex=1 TO starsHere:GOSUB findEmptySector:sectorSymbol$=" * ":placeX=randomX:placeY=randomY:GOSUB insertInQuadrantMap:NEXT starIndex
1980 shortRangeScanCommand: GOSUB shortRangeScan
1990 commandLoop: IF shields+energy>10 THEN IF energy>10 OR deviceDamage(7)=0 THEN readCommand
2020 PRINT:PRINT"** FATAL ERROR **   YOU'VE JUST STRANDED YOUR SHIP IN "
2030 PRINT"SPACE":PRINT"YOU HAVE INSUFFICIENT MANEUVERING ENERGY,";
2040 PRINT" AND SHIELD CONTROL":PRINT"IS PRESENTLY INCAPABLE OF CROSS";
2050 PRINT"-CIRCUITING TO ENGINE ROOM!!":GOTO endOfGameStardate
2060 readCommand: INPUT"COMMAND? ";commandText$
2080 FOR commandIndex=1 TO 9:IF LEFT$(commandText$,3)<>MID$(commandNames$,3*commandIndex-2,3) THEN tryNextCommand
2140 ON commandIndex GOTO courseControl,shortRangeScanCommand,longRangeScan,phaserControl,photonTorpedoControl,shieldControl,damageControl,libraryComputer,endOfMission
2160 tryNextCommand: NEXT commandIndex:PRINT"ENTER ONE OF THE FOLLOWING:"
2180 PRINT"  NAV  (TO SET COURSE)"
2190 PRINT"  SRS  (FOR SHORT RANGE SENSOR SCAN)"
2200 PRINT"  LRS  (FOR LONG RANGE SENSOR SCAN)"
2210 PRINT"  PHA  (TO FIRE PHASERS)"
2220 PRINT"  TOR  (TO FIRE PHOTON TORPEDOES)"
2230 PRINT"  SHE  (TO RAISE OR LOWER SHIELDS)"
2240 PRINT"  DAM  (FOR DAMAGE CONTROL REPORTS)"
2250 PRINT"  COM  (TO CALL ON LIBRARY-COMPUTER)"
2260 PRINT"  XXX  (TO RESIGN YOUR COMMAND)":PRINT:GOTO commandLoop
2290 REM COURSE CONTROL BEGINS HERE
2300 courseControl: INPUT"COURSE (0-9)? ";course:IF course=9 THEN course=1
2310 IF course>=1 AND course<9 THEN askWarpFactor
2330 PRINT"   LT. SULU REPORTS, 'INCORRECT COURSE DATA, SIR!'":GOTO commandLoop
2350 askWarpFactor: maxWarp$="8":IF deviceDamage(1)<0 THEN maxWarp$="0.2"
2360 PRINT"WARP FACTOR (0-";maxWarp$;")";:INPUT warpFactor:IF deviceDamage(1)<0 AND warpFactor>.2 THEN warpEnginesDamaged
2380 IF warpFactor>0 AND warpFactor<=8 THEN checkWarpEnergy
2390 IF warpFactor=0 THEN commandLoop
2420 PRINT"   CHIEF ENGINEER SCOTT REPORTS 'THE ENGINES WON'T TAKE";
2430 PRINT" WARP ";" ";warpFactor;" ";"!'":GOTO commandLoop
2470 warpEnginesDamaged: PRINT"WARP ENGINES ARE DAMAGED.  MAXIUM SPEED = WARP 0.2":GOTO commandLoop
2490 checkWarpEnergy: warpEnergy=INT(warpFactor*8+.5):IF energy-warpEnergy>=0 THEN klingonsMoveAndFire
2500 PRINT"ENGINEERING REPORTS   'INSUFFICIENT ENERGY AVAILABLE"
2510 PRINT"                       FOR MANEUVERING AT WARP";" ";warpFactor;" ";"!'"
2530 IF shields<warpEnergy-energy OR deviceDamage(7)<0 THEN commandLoop
2550 PRINT"DEFLECTOR CONTROL ROOM ACKNOWLEDGES";" ";shields;" ";"UNITS OF ENERGY"
2560 PRINT"                         PRESENTLY DEPLOYED TO SHIELDS."
2570 GOTO commandLoop
2580 REM KLINGONS MOVE/FIRE ON MOVING STARSHIP . . .
2590 klingonsMoveAndFire: FOR klingonIndex=1 TO klingonsHere:IF klingon(klingonIndex,3)=0 THEN nextKlingonMove
2610 sectorSymbol$="   ":placeX=klingon(klingonIndex,1):placeY=klingon(klingonIndex,2):GOSUB insertInQuadrantMap:GOSUB findEmptySector
2660 klingon(klingonIndex,1)=placeX:klingon(klingonIndex,2)=placeY:sectorSymbol$="+K+":GOSUB insertInQuadrantMap
2700 nextKlingonMove: NEXT klingonIndex:GOSUB klingonsShoot:damageReported=0:repairIncrement=warpFactor:IF warpFactor>=1 THEN repairIncrement=1
2770 FOR deviceIndex=1 TO 8:IF deviceDamage(deviceIndex)>=0 THEN nextDeviceRepair
2790 deviceDamage(deviceIndex)=deviceDamage(deviceIndex)+repairIncrement:IF deviceDamage(deviceIndex)>-.1 AND deviceDamage(deviceIndex)<0 THEN deviceDamage(deviceIndex)=-.1:GOTO nextDeviceRepair
2800 IF deviceDamage(deviceIndex)<0 THEN nextDeviceRepair
2810 IF damageReported<>1 THEN damageReported=1:PRINT"DAMAGE CONTROL REPORT:  ";
2840 PRINT TAB(8);:deviceNumber=deviceIndex:GOSUB deviceNameLookup:PRINT placeName$;" REPAIR COMPLETED."
2880 nextDeviceRepair: NEXT deviceIndex:IF RND(1)>.2 THEN beginMovingStarship
2910 deviceNumber=FNrandomSector(1):IF RND(1)>=.6 THEN randomRepairImproved
2930 deviceDamage(deviceNumber)=deviceDamage(deviceNumber)-(RND(1)*5+1):PRINT"DAMAGE CONTROL REPORT:  ";
2960 GOSUB deviceNameLookup:PRINT placeName$;" DAMAGED":PRINT:GOTO beginMovingStarship
3000 randomRepairImproved: deviceDamage(deviceNumber)=deviceDamage(deviceNumber)+RND(1)*3+1:PRINT"DAMAGE CONTROL REPORT:  ";
3030 GOSUB deviceNameLookup:PRINT placeName$;" STATE OF REPAIR IMPROVED":PRINT
3060 REM BEGIN MOVING STARSHIP
3070 beginMovingStarship: sectorSymbol$="   ":placeX=INT(sectorX):placeY=INT(sectorY):GOSUB insertInQuadrantMap
3110 courseStepX=courseVector(course,1)+(courseVector(course+1,1)-courseVector(course,1))*(course-INT(course)):galacticX=sectorX:galacticY=sectorY
3140 courseStepY=courseVector(course,2)+(courseVector(course+1,2)-courseVector(course,2))*(course-INT(course)):oldQuadrantX=quadrantX:oldQuadrantY=quadrantY
3170 FOR stepIndex=1 TO warpEnergy:sectorX=sectorX+courseStepX:sectorY=sectorY+courseStepY:IF sectorX<1 OR sectorX>=9 OR sectorY<1 OR sectorY>=9 THEN crossQuadrantBoundary
3240 mapIndex=INT(sectorX)*24+INT(sectorY)*3-26:IF MID$(quadrantMap$,mapIndex,2)="  " THEN nextWarpStep
3320 sectorX=INT(sectorX-courseStepX):sectorY=INT(sectorY-courseStepY):PRINT"WARP ENGINES SHUT DOWN AT ";
3350 PRINT"SECTOR";" ";sectorX;" ";",";" ";sectorY;" ";"DUE TO BAD NAVAGATION":GOTO arriveAtSector
3360 nextWarpStep: NEXT stepIndex:sectorX=INT(sectorX):sectorY=INT(sectorY)
3370 arriveAtSector: sectorSymbol$="<*>":placeX=INT(sectorX):placeY=INT(sectorY):GOSUB insertInQuadrantMap:GOSUB maneuverEnergy:timeUsed=1
3430 IF warpFactor<1 THEN timeUsed=.1*INT(10*warpFactor)
3450 stardate=stardate+timeUsed:IF stardate>startStardate+missionDays THEN endOfGameStardate
3470 REM SEE IF DOCKED, THEN GET COMMAND
3480 GOTO shortRangeScanCommand
3490 REM EXCEEDED QUADRANT LIMITS
3500 crossQuadrantBoundary: galacticX=8*quadrantX+galacticX+warpEnergy*courseStepX:galacticY=8*quadrantY+galacticY+warpEnergy*courseStepY:quadrantX=INT(galacticX/8):quadrantY=INT(galacticY/8):sectorX=INT(galacticX-quadrantX*8)
3550 sectorY=INT(galacticY-quadrantY*8):IF sectorX=0 THEN quadrantX=quadrantX-1:sectorX=8
3590 IF sectorY=0 THEN quadrantY=quadrantY-1:sectorY=8
3620 edgeHit=0:IF quadrantX<1 THEN edgeHit=1:quadrantX=1:sectorX=1
3670 IF quadrantX>8 THEN edgeHit=1:quadrantX=8:sectorX=8
3710 IF quadrantY<1 THEN edgeHit=1:quadrantY=1:sectorY=1
3750 IF quadrantY>8 THEN edgeHit=1:quadrantY=8:sectorY=8
3790 IF edgeHit=0 THEN checkQuadrantChange
3800 PRINT"LT. UHURA REPORTS MESSAGE FROM STARFLEET COMMAND:"
3810 PRINT"  'PERMISSION TO ATTEMPT CROSSING OF GALACTIC PERIMETER"
3820 PRINT"  IS HEREBY *DENIED*.  SHUT DOWN YOUR ENGINES.'"
3830 PRINT"CHIEF ENGINEER SCOTT REPORTS  'WARP ENGINES SHUT DOWN"
3840 PRINT"  AT SECTOR";" ";sectorX;" ";",";" ";sectorY;" ";"OF QUADRANT";" ";quadrantX;" ";",";" ";quadrantY;" ";".'"
3850 IF stardate>startStardate+missionDays THEN endOfGameStardate
3860 checkQuadrantChange: IF 8*quadrantX+quadrantY=8*oldQuadrantX+oldQuadrantY THEN arriveAtSector
3870 stardate=stardate+1:GOSUB maneuverEnergy:GOTO enterQuadrant
3900 REM MANEUVER ENERGY S/R **
3910 maneuverEnergy: energy=energy-warpEnergy-10:IF energy>=0 THEN RETURN
3930 PRINT"SHIELD CONTROL SUPPLIES ENERGY TO COMPLETE THE MANEUVER."
3940 shields=shields+energy:energy=0:IF shields<=0 THEN shields=0
3980 RETURN
3990 REM LONG RANGE SENSOR SCAN CODE
4000 longRangeScan: IF deviceDamage(3)<0 THEN PRINT"LONG RANGE SENSORS ARE INOPERABLE":GOTO commandLoop
4030 PRINT"LONG RANGE SCAN FOR QUADRANT";" ";quadrantX;" ";",";" ";quadrantY;" "
4040 borderLine$="-------------------":PRINT borderLine$
4060 FOR scanQuadrantX=quadrantX-1 TO quadrantX+1:scanCell(1)=-1:scanCell(2)=-2:scanCell(3)=-3:FOR scanQuadrantY=quadrantY-1 TO quadrantY+1
4120 IF scanQuadrantX>0 AND scanQuadrantX<9 AND scanQuadrantY>0 AND scanQuadrantY<9 THEN scanCell(scanQuadrantY-quadrantY+2)=galaxy(scanQuadrantX,scanQuadrantY):chartedGalaxy(scanQuadrantX,scanQuadrantY)=galaxy(scanQuadrantX,scanQuadrantY)
4180 NEXT scanQuadrantY:FOR scanColumn=1 TO 3:PRINT": ";:IF scanCell(scanColumn)<0 THEN PRINT"*** ";:GOTO nextLongRangeCell
4210 PRINT RIGHT$(STR$(scanCell(scanColumn)+1000),3);" ";
4230 nextLongRangeCell: NEXT scanColumn:PRINT":":PRINT borderLine$:NEXT scanQuadrantX:GOTO commandLoop
4250 REM PHASER CONTROL CODE BEGINS HERE
4260 phaserControl: IF deviceDamage(4)<0 THEN PRINT"PHASERS INOPERATIVE":GOTO commandLoop
4265 IF klingonsHere>0 THEN checkComputerForPhasers
4270 reportNoEnemies: PRINT"SCIENCE OFFICER SPOCK REPORTS  'SENSORS SHOW NO ENEMY SHIPS"
4280 PRINT"                                IN THIS QUADRANT'":GOTO commandLoop
4330 checkComputerForPhasers: IF deviceDamage(8)<0 THEN PRINT"COMPUTER FAILURE HAMPERS ACCURACY"
4350 PRINT"PHASERS LOCKED ON TARGET;  ";
4360 showPhaserEnergy: PRINT"ENERGY AVAILABLE =";" ";energy;" ";"UNITS"
4370 INPUT"NUMBER OF UNITS TO FIRE? ";phaserUnits:IF phaserUnits<=0 THEN commandLoop
4400 IF energy-phaserUnits<0 THEN showPhaserEnergy
4410 energy=energy-phaserUnits:IF deviceDamage(7)<0 THEN phaserUnits=phaserUnits*RND(1)
4450 energyPerKlingon=INT(phaserUnits/klingonsHere):FOR klingonIndex=1 TO 3:IF klingon(klingonIndex,3)<=0 THEN nextKlingonPhaser
4480 hitEnergy=INT((energyPerKlingon/FNdistance(0))*(RND(1)+2)):IF hitEnergy>.15*klingon(klingonIndex,3) THEN applyPhaserHit
4500 PRINT"SENSORS SHOW NO DAMAGE TO ENEMY AT ";" ";klingon(klingonIndex,1);" ";",";" ";klingon(klingonIndex,2);" ":GOTO nextKlingonPhaser
4530 applyPhaserHit: klingon(klingonIndex,3)=klingon(klingonIndex,3)-hitEnergy:PRINT " ";hitEnergy;" ";"UNIT HIT ON KLINGON AT SECTOR";" ";klingon(klingonIndex,1);" ";",";
4550 PRINT " ";klingon(klingonIndex,2);" ":IF klingon(klingonIndex,3)<=0 THEN PRINT"*** KLINGON DESTROYED ***":GOTO klingonDestroyedByPhasers
4560 PRINT"   (SENSORS SHOW";" ";klingon(klingonIndex,3);" ";"UNITS REMAINING)":GOTO nextKlingonPhaser
4580 klingonDestroyedByPhasers: klingonsHere=klingonsHere-1:klingonsLeft=klingonsLeft-1:placeX=klingon(klingonIndex,1):placeY=klingon(klingonIndex,2):sectorSymbol$="   ":GOSUB insertInQuadrantMap
4650 klingon(klingonIndex,3)=0:galaxy(quadrantX,quadrantY)=galaxy(quadrantX,quadrantY)-100:chartedGalaxy(quadrantX,quadrantY)=galaxy(quadrantX,quadrantY):IF klingonsLeft<=0 THEN allKlingonsDestroyed
4670 nextKlingonPhaser: NEXT klingonIndex:GOSUB klingonsShoot:GOTO commandLoop
4690 REM PHOTON TORPEDO CODE BEGINS HERE
4700 photonTorpedoControl: IF torpedoes<=0 THEN PRINT"ALL PHOTON TORPEDOES EXPENDED":GOTO commandLoop
4730 IF deviceDamage(5)<0 THEN PRINT"PHOTON TUBES ARE NOT OPERATIONAL":GOTO commandLoop
4760 askTorpedoCourse: INPUT"PHOTON TORPEDO COURSE (1-9)? ";course:IF course=9 THEN course=1
4780 IF course>=1 AND course<9 THEN fireTorpedo
4790 PRINT"ENSIGN CHEKOV REPORTS,  'INCORRECT COURSE DATA, SIR!'"
4800 GOTO commandLoop
4850 fireTorpedo: courseStepX=courseVector(course,1)+(courseVector(course+1,1)-courseVector(course,1))*(course-INT(course)):energy=energy-2:torpedoes=torpedoes-1
4860 courseStepY=courseVector(course,2)+(courseVector(course+1,2)-courseVector(course,2))*(course-INT(course)):torpedoX=sectorX:torpedoY=sectorY
4910 PRINT"TORPEDO TRACK:"
4920 advanceTorpedo: torpedoX=torpedoX+courseStepX:torpedoY=torpedoY+courseStepY:torpedoSectorX=INT(torpedoX+.5):torpedoSectorY=INT(torpedoY+.5)
4960 IF torpedoSectorX<1 OR torpedoSectorX>8 OR torpedoSectorY<1 OR torpedoSectorY>8 THEN torpedoMissed
5000 PRINT"               ";" ";torpedoSectorX;" ";",";" ";torpedoSectorY;" ":sectorSymbol$="   ":placeX=torpedoX:placeY=torpedoY:GOSUB compareQuadrantMap
5050 IF symbolFound<>0 THEN advanceTorpedo
5060 sectorSymbol$="+K+":placeX=torpedoX:placeY=torpedoY:GOSUB compareQuadrantMap:IF symbolFound=0 THEN torpedoCheckStar
5110 PRINT"*** KLINGON DESTROYED ***":klingonsHere=klingonsHere-1:klingonsLeft=klingonsLeft-1:IF klingonsLeft<=0 THEN allKlingonsDestroyed
5150 FOR klingonIndex=1 TO 3:IF torpedoSectorX=klingon(klingonIndex,1) AND torpedoSectorY=klingon(klingonIndex,2) THEN removeDestroyedKlingon
5180 NEXT klingonIndex:klingonIndex=3
5190 removeDestroyedKlingon: klingon(klingonIndex,3)=0:GOTO torpedoUpdateMap
5210 torpedoCheckStar: sectorSymbol$=" * ":placeX=torpedoX:placeY=torpedoY:GOSUB compareQuadrantMap:IF symbolFound=0 THEN torpedoCheckStarbase
5260 PRINT"STAR AT";" ";torpedoSectorX;" ";",";" ";torpedoSectorY;" ";"ABSORBED TORPEDO ENERGY.":GOSUB klingonsShoot:GOTO commandLoop
5280 torpedoCheckStarbase: sectorSymbol$=">!<":placeX=torpedoX:placeY=torpedoY:GOSUB compareQuadrantMap:IF symbolFound=0 THEN askTorpedoCourse
5330 PRINT"*** STARBASE DESTROYED ***":starbasesHere=starbasesHere-1:starbasesLeft=starbasesLeft-1
5360 IF starbasesLeft>0 OR klingonsLeft>stardate-startStardate-missionDays THEN courtMartialWarning
5370 PRINT"THAT DOES IT, CAPTAIN!!YOU ARE HEREBY RELIEVED OF COMMAND"
5380 PRINT"AND SENTENCED TO 99 STARDATES AT HARD LABOR ON CYGNUS 12!!"
5390 GOTO endOfMission
5400 courtMartialWarning: PRINT"STARFLEET COMMAND REVIEWING YOUR RECORD TO CONSIDER"
5410 PRINT"COURT MARTIAL!":docked=0
5430 torpedoUpdateMap: placeX=torpedoX:placeY=torpedoY:sectorSymbol$="   ":GOSUB insertInQuadrantMap
5470 galaxy(quadrantX,quadrantY)=klingonsHere*100+starbasesHere*10+starsHere:chartedGalaxy(quadrantX,quadrantY)=galaxy(quadrantX,quadrantY):GOSUB klingonsShoot:GOTO commandLoop
5490 torpedoMissed: PRINT"TORPEDO MISSED":GOSUB klingonsShoot:GOTO commandLoop
5520 REM SHIELD CONTROL
5530 shieldControl: IF deviceDamage(7)<0 THEN PRINT"SHIELD CONTROL INOPERABLE":GOTO commandLoop
5560 PRINT"ENERGY AVAILABLE =";" ";energy+shields;" ";:INPUT"NUMBER OF UNITS TO SHIELDS? ";shieldUnits
5580 IF shieldUnits<0 OR shields=shieldUnits THEN PRINT"<SHIELDS UNCHANGED>":GOTO commandLoop
5590 IF shieldUnits<=energy+shields THEN setShields
5600 PRINT"SHIELD CONTROL REPORTS  'THIS IS NOT THE FEDERATION TREASURY.'"
5610 PRINT"<SHIELDS UNCHANGED>":GOTO commandLoop
5630 setShields: energy=energy+shields-shieldUnits:shields=shieldUnits:PRINT"DEFLECTOR CONTROL ROOM REPORT:"
5660 PRINT"  'SHIELDS NOW AT";" ";INT(shields);" ";"UNITS PER YOUR COMMAND.'":GOTO commandLoop
5680 REM DAMAGE CONTROL
5690 damageControl: IF deviceDamage(6)>=0 THEN printDamageReport
5700 PRINT"DAMAGE CONTROL REPORT NOT AVAILABLE":IF docked=0 THEN commandLoop
5720 estimateRepairTime: repairTime=0:FOR deviceIndex=1 TO 8:IF deviceDamage(deviceIndex)<0 THEN repairTime=repairTime+.1
5760 NEXT deviceIndex:IF repairTime=0 THEN commandLoop
5780 PRINT:repairTime=repairTime+repairBonus:IF repairTime>=1 THEN repairTime=.9
5810 PRINT"TECHNICIANS STANDING BY TO EFFECT REPAIRS TO YOUR SHIP;"
5820 PRINT"ESTIMATED TIME TO REPAIR:";" ";.01*INT(100*repairTime);" ";"STARDATES"
5840 INPUT "WILL YOU AUTHORIZE THE REPAIR ORDER (Y/N)? ";answer$
5860 IF answer$<>"Y" THEN commandLoop
5870 FOR deviceIndex=1 TO 8:IF deviceDamage(deviceIndex)<0 THEN deviceDamage(deviceIndex)=0
5890 NEXT deviceIndex:stardate=stardate+repairTime+.1
5910 printDamageReport: PRINT:PRINT"DEVICE             STATE OF REPAIR":FOR deviceNumber=1 TO 8
5920 GOSUB deviceNameLookup:PRINT placeName$;LEFT$(spaces$,25-LEN(placeName$));" ";INT(deviceDamage(deviceNumber)*100)*.01;" "
5950 NEXT deviceNumber:PRINT:IF docked<>0 THEN estimateRepairTime
5980 GOTO commandLoop
5990 REM KLINGONS SHOOTING
6000 klingonsShoot: IF klingonsHere<=0 THEN RETURN
6010 IF docked<>0 THEN PRINT"STARBASE SHIELDS PROTECT THE ENTERPRISE":RETURN
6040 FOR klingonIndex=1 TO 3:IF klingon(klingonIndex,3)<=0 THEN nextKlingonShot
6060 hitEnergy=INT((klingon(klingonIndex,3)/FNdistance(1))*(2+RND(1))):shields=shields-hitEnergy:klingon(klingonIndex,3)=klingon(klingonIndex,3)/(3+RND(0))
6080 PRINT " ";hitEnergy;" ";"UNIT HIT ON ENTERPRISE FROM SECTOR";" ";klingon(klingonIndex,1);" ";",";" ";klingon(klingonIndex,2);" "
6090 IF shields<=0 THEN enterpriseDestroyed
6100 PRINT"      <SHIELDS DOWN TO";" ";shields;" ";"UNITS>":IF hitEnergy<20 THEN nextKlingonShot
6120 IF RND(1)>.6 OR hitEnergy/shields<=.02 THEN nextKlingonShot
6140 deviceNumber=FNrandomSector(1):deviceDamage(deviceNumber)=deviceDamage(deviceNumber)-hitEnergy/shields-.5*RND(1):GOSUB deviceNameLookup
6170 PRINT"DAMAGE CONTROL REPORTS ";placeName$;" DAMAGED BY THE HIT'"
6200 nextKlingonShot: NEXT klingonIndex:RETURN
6210 REM END OF GAME
6220 endOfGameStardate: PRINT"IT IS STARDATE";" ";stardate;" ":GOTO endOfMission
6240 enterpriseDestroyed: PRINT:PRINT"THE ENTERPRISE HAS BEEN DESTROYED.  THEN FEDERATION ";
6250 PRINT"WILL BE CONQUERED":GOTO endOfGameStardate
6270 endOfMission: PRINT"THERE WERE";" ";klingonsLeft;" ";"KLINGON BATTLE CRUISERS LEFT AT"
6280 PRINT"THE END OF YOUR MISSION."
6290 askNewCommander: PRINT:PRINT:IF starbasesLeft=0 THEN endProgram
6310 PRINT"THE FEDERATION IS IN NEED OF A NEW STARSHIP COMMANDER"
6320 PRINT"FOR A SIMILAR MISSION -- IF THERE IS A VOLUNTEER,"
6330 INPUT"LET HIM STEP FORWARD AND ENTER 'AYE'? ";answer$:IF answer$="AYE" THEN restartGame
6360 endProgram: END
6370 allKlingonsDestroyed: PRINT"CONGRULATION, CAPTAIN!THEN LAST KLINGON BATTLE CRUISER"
6380 PRINT"MENACING THE FDERATION HAS BEEN DESTROYED.":PRINT
6400 PRINT"YOUR EFFICIENCY RATING IS";" ";1000*(klingonsAtStart/(stardate-startStardate))^2;" ":GOTO askNewCommander
6420 REM SHORT RANGE SENSOR SCAN & STARTUP SUBROUTINE
6430 shortRangeScan: FOR scanSectorX=sectorX-1 TO sectorX+1:FOR scanSectorY=sectorY-1 TO sectorY+1
6450 IF INT(scanSectorX+.5)<1 OR INT(scanSectorX+.5)>8 OR INT(scanSectorY+.5)<1 OR INT(scanSectorY+.5)>8 THEN nextSectorScan
6490 sectorSymbol$=">!<":placeX=scanSectorX:placeY=scanSectorY:GOSUB compareQuadrantMap:IF symbolFound=1 THEN dockedAtStarbase
6540 nextSectorScan: NEXT scanSectorY:NEXT scanSectorX:docked=0:GOTO setCondition
6580 dockedAtStarbase: docked=1:condition$="DOCKED":energy=energyAtStart:torpedoes=torpedoesAtStart
6620 PRINT"SHIELDS DROPPED FOR DOCKING PURPOSES":shields=0:GOTO checkSensorsOperational
6650 setCondition: IF klingonsHere>0 THEN condition$="*RED*":GOTO checkSensorsOperational
6660 condition$="GREEN":IF energy<energyAtStart*.1 THEN condition$="YELLOW"
6720 checkSensorsOperational: IF deviceDamage(2)>=0 THEN drawShortRangeScan
6730 PRINT:PRINT"*** SHORT RANGE SENSORS ARE OUT ***":PRINT:RETURN
6770 drawShortRangeScan: borderLine$="---------------------------------":PRINT borderLine$:FOR displayRow=1 TO 8
6820 FOR mapCharIndex=(displayRow-1)*24+1 TO (displayRow-1)*24+22 STEP 3:PRINT" ";MID$(quadrantMap$,mapCharIndex,3);:NEXT mapCharIndex
6830 ON displayRow GOTO statusStardate,statusCondition,statusQuadrant,statusSector,statusTorpedoes,statusEnergy,statusShields,statusKlingons
6850 statusStardate: PRINT"        STARDATE          ";" ";INT(stardate*10)*.1;" ":GOTO nextScanRow
6900 statusCondition: PRINT"        CONDITION          ";condition$:GOTO nextScanRow
6960 statusQuadrant: PRINT"        QUADRANT          ";" ";quadrantX;" ";",";" ";quadrantY;" ":GOTO nextScanRow
7020 statusSector: PRINT"        SECTOR            ";" ";sectorX;" ";",";" ";sectorY;" ":GOTO nextScanRow
7070 statusTorpedoes: PRINT"        PHOTON TORPEDOES  ";" ";INT(torpedoes);" ":GOTO nextScanRow
7120 statusEnergy: PRINT"        TOTAL ENERGY      ";" ";INT(energy+shields);" ":GOTO nextScanRow
7180 statusShields: PRINT"        SHIELDS           ";" ";INT(shields);" ":GOTO nextScanRow
7240 statusKlingons: PRINT"        KLINGONS REMAINING";" ";INT(klingonsLeft);" "
7260 nextScanRow: NEXT displayRow:PRINT borderLine$:RETURN
7280 REM LIBRARY COMPUTER CODE
7290 libraryComputer: IF deviceDamage(8)<0 THEN PRINT"COMPUTER DISABLED":GOTO commandLoop
7320 computerPrompt: INPUT"COMPUTER ACTIVE AND AWAITING COMMAND? ";computerFunction:IF computerFunction<0 THEN commandLoop
7350 PRINT:computerMode=1:ON computerFunction+1 GOTO cumulativeGalacticRecord,statusReport,torpedoData,starbaseNavData,directionCalculator,galaxyMapSetup
7360 PRINT"FUNCTIONS AVAILABLE FROM LIBRARY-COMPUTER:"
7370 PRINT"   0 = CUMULATIVE GALACTIC RECORD"
7372 PRINT"   1 = STATUS REPORT"
7374 PRINT"   2 = PHOTON TORPEDO DATA"
7376 PRINT"   3 = STARBASE NAV DATA"
7378 PRINT"   4 = DIRECTION/DISTANCE CALCULATOR"
7380 PRINT"   5 = GALAXY 'REGION NAME' MAP":PRINT:GOTO computerPrompt
7390 REM SETUP TO CHANGE CUM GAL RECORD TO GALAXY MAP
7400 galaxyMapSetup: computerMode=0:regionNameOnly=1:PRINT"                        THE GALAXY":GOTO galacticRecordHeader
7530 REM CUM GALACTIC RECORD
7540 cumulativeGalacticRecord: REM INPUT"DO YOU WANT A HARDCOPY? IS THE TTY ON (Y/N)";A$
7542 REM IFA$="Y"THENPOKE1229,2:POKE1237,3:NULL1
7543 PRINT:PRINT"        ";
7544 PRINT"COMPUTER RECORD OF GALAXY FOR QUADRANT";" ";quadrantX;" ";",";" ";quadrantY;" "
7546 PRINT
7550 galacticRecordHeader: PRINT"       1     2     3     4     5     6     7     8"
7560 borderLine$="     ----- ----- ----- ----- ----- ----- ----- -----"
7570 PRINT borderLine$:FOR recordRow=1 TO 8:PRINT " ";recordRow;" ";:IF computerMode=0 THEN printRegionNames
7630 FOR recordColumn=1 TO 8:PRINT"   ";:IF chartedGalaxy(recordRow,recordColumn)=0 THEN PRINT"***";:GOTO nextRecordCell
7700 PRINT RIGHT$(STR$(chartedGalaxy(recordRow,recordColumn)+1000),3);
7720 nextRecordCell: NEXT recordColumn:GOTO nextRecordRow
7740 printRegionNames: nameQuadrantX=recordRow:nameQuadrantY=1:GOSUB quadrantNameLookup:nameColumn=INT(15-.5*LEN(placeName$)):PRINT TAB(nameColumn);placeName$;
7800 nameQuadrantY=5:GOSUB quadrantNameLookup:nameColumn=INT(39-.5*LEN(placeName$)):PRINT TAB(nameColumn);placeName$;
7850 nextRecordRow: PRINT:PRINT borderLine$:NEXT recordRow:PRINT:GOTO commandLoop
7890 REM STATUS REPORT
7900 statusReport: PRINT "   STATUS REPORT:":plural$="":IF klingonsLeft>1 THEN plural$="S"
7940 PRINT"KLINGON";plural$;" LEFT: ";" ";klingonsLeft;" "
7960 PRINT"MISSION MUST BE COMPLETED IN";" ";.1*INT((startStardate+missionDays-stardate)*10);" ";"STARDATES"
7970 plural$="S":IF starbasesLeft<2 THEN plural$="":IF starbasesLeft<1 THEN noStarbasesLeft
7980 PRINT"THE FEDERATION IS MAINTAINING";" ";starbasesLeft;" ";"STARBASE";plural$;" IN THE GALAXY"
7990 GOTO damageControl
8010 noStarbasesLeft: PRINT"YOUR STUPIDITY HAS LEFT YOU ON YOUR ON IN"
8020 PRINT"  THE GALAXY -- YOU HAVE NO STARBASES LEFT!":GOTO damageControl
8060 REM TORPEDO, BASE NAV, D/D CALCULATOR
8070 torpedoData: IF klingonsHere<=0 THEN reportNoEnemies
8080 plural$="":IF klingonsHere>1 THEN plural$="S"
8090 PRINT"FROM ENTERPRISE TO KLINGON BATTLE CRUSER";plural$
8100 computerMode=0:FOR klingonIndex=1 TO 3:IF klingon(klingonIndex,3)<=0 THEN nextTargetKlingon
8110 toX=klingon(klingonIndex,1):deltaY=klingon(klingonIndex,2)
8120 directionFromShip: directionBase=sectorX:deltaX=sectorY:GOTO computeDirection
8150 directionCalculator: PRINT"DIRECTION/DISTANCE CALCULATOR:"
8160 PRINT"YOU ARE AT QUADRANT ";" ";quadrantX;" ";",";" ";quadrantY;" ";" SECTOR ";" ";sectorX;" ";",";" ";sectorY;" "
8170 PRINT"PLEASE ENTER":INPUT"  INITIAL COORDINATES (X,Y)? ";directionBase,deltaX
8200 INPUT"  FINAL COORDINATES (X,Y)? ";toX,deltaY
8220 computeDirection: deltaY=deltaY-deltaX:deltaX=directionBase-toX:IF deltaY<0 THEN directionLeft
8250 IF deltaX<0 THEN directionDown
8260 IF deltaY>0 THEN directionBaseOne
8270 IF deltaX=0 THEN directionBase=5:GOTO compareAxes
8280 directionBaseOne: directionBase=1
8290 compareAxes: IF ABS(deltaX)<=ABS(deltaY) THEN directionMinorAxis
8310 PRINT"DIRECTION =";" ";directionBase+(((ABS(deltaX)-ABS(deltaY))+ABS(deltaX))/ABS(deltaX));" ":GOTO printDistance
8330 directionMinorAxis: PRINT"DIRECTION =";" ";directionBase+(ABS(deltaX)/ABS(deltaY));" ":GOTO printDistance
8350 directionLeft: IF deltaX>0 THEN directionBase=3:GOTO compareAxesBackward
8360 IF deltaY<>0 THEN directionBase=5:GOTO compareAxes
8410 directionDown: directionBase=7
8420 compareAxesBackward: IF ABS(deltaX)>=ABS(deltaY) THEN directionMinorAxisBackward
8430 PRINT"DIRECTION =";" ";directionBase+(((ABS(deltaY)-ABS(deltaX))+ABS(deltaY))/ABS(deltaY));" ":GOTO printDistance
8450 directionMinorAxisBackward: PRINT"DIRECTION =";" ";directionBase+(ABS(deltaY)/ABS(deltaX));" "
8460 printDistance: PRINT"DISTANCE =";" ";SQR(deltaY^2+deltaX^2);" ":IF computerMode=1 THEN commandLoop
8480 nextTargetKlingon: NEXT klingonIndex:GOTO commandLoop
8500 starbaseNavData: IF starbasesHere<>0 THEN PRINT"FROM ENTERPRISE TO STARBASE:":toX=starbaseX:deltaY=starbaseY:GOTO directionFromShip
8510 PRINT"MR. SPOCK REPORTS,  'SENSORS SHOW NO STARBASES IN THIS";
8520 PRINT" QUADRANT.'":GOTO commandLoop
8580 REM FIND EMPTY PLACE IN QUADRANT (FOR THINGS)
8590 findEmptySector: randomX=FNrandomSector(1):randomY=FNrandomSector(1):sectorSymbol$="   ":placeX=randomX:placeY=randomY:GOSUB compareQuadrantMap:IF symbolFound=0 THEN findEmptySector
8600 RETURN
8660 REM INSERT IN STRING ARRAY FOR QUADRANT
8670 insertInQuadrantMap: mapIndex=INT(placeY-.5)*3+INT(placeX-.5)*24+1
8675 IF LEN(sectorSymbol$)<>3 THEN PRINT"ERROR":STOP
8680 IF mapIndex=1 THEN quadrantMap$=sectorSymbol$+RIGHT$(quadrantMap$,189):RETURN
8690 IF mapIndex=190 THEN quadrantMap$=LEFT$(quadrantMap$,189)+sectorSymbol$:RETURN
8700 quadrantMap$=LEFT$(quadrantMap$,mapIndex-1)+sectorSymbol$+RIGHT$(quadrantMap$,190-mapIndex):RETURN
8780 REM PRINTS DEVICE NAME
8790 deviceNameLookup: ON deviceNumber GOTO deviceNameWarpEngines,deviceNameShortRange,deviceNameLongRange,deviceNamePhasers,deviceNamePhotonTubes,deviceNameDamageControl,deviceNameShieldControl,deviceNameComputer
8792 deviceNameWarpEngines: placeName$="WARP ENGINES":RETURN
8794 deviceNameShortRange: placeName$="SHORT RANGE SENSORS":RETURN
8796 deviceNameLongRange: placeName$="LONG RANGE SENSORS":RETURN
8798 deviceNamePhasers: placeName$="PHASER CONTROL":RETURN
8800 deviceNamePhotonTubes: placeName$="PHOTON TUBES":RETURN
8802 deviceNameDamageControl: placeName$="DAMAGE CONTROL":RETURN
8804 deviceNameShieldControl: placeName$="SHIELD CONTROL":RETURN
8806 deviceNameComputer: placeName$="LIBRARY-COMPUTER":RETURN
8820 REM STRING COMPARISON IN QUADRANT ARRAY
8830 compareQuadrantMap: placeX=INT(placeX+.5):placeY=INT(placeY+.5):mapIndex=(placeY-1)*3+(placeX-1)*24+1:symbolFound=0
8890 IF MID$(quadrantMap$,mapIndex,3)<>sectorSymbol$ THEN RETURN
8900 symbolFound=1:RETURN
9010 REM QUADRANT NAME IN G2$ FROM Z4,Z5 (=Q1,Q2)
9020 REM CALL WITH G5=1 TO GET REGION NAME ONLY
9030 quadrantNameLookup: IF nameQuadrantY<=4 THEN ON nameQuadrantX GOTO regionAntares,regionRigel,regionProcyon,regionVega,regionCanopus,regionAltair,regionSagittarius,regionPollux
9035 GOTO secondHalfRegions
9040 regionAntares: placeName$="ANTARES":GOTO appendQuadrantNumber
9050 regionRigel: placeName$="RIGEL":GOTO appendQuadrantNumber
9060 regionProcyon: placeName$="PROCYON":GOTO appendQuadrantNumber
9070 regionVega: placeName$="VEGA":GOTO appendQuadrantNumber
9080 regionCanopus: placeName$="CANOPUS":GOTO appendQuadrantNumber
9090 regionAltair: placeName$="ALTAIR":GOTO appendQuadrantNumber
9100 regionSagittarius: placeName$="SAGITTARIUS":GOTO appendQuadrantNumber
9110 regionPollux: placeName$="POLLUX":GOTO appendQuadrantNumber
9120 secondHalfRegions: ON nameQuadrantX GOTO regionSirius,regionDeneb,regionCapella,regionBetelgeuse,regionAldebaran,regionRegulus,regionArcturus,regionSpica
9130 regionSirius: placeName$="SIRIUS":GOTO appendQuadrantNumber
9140 regionDeneb: placeName$="DENEB":GOTO appendQuadrantNumber
9150 regionCapella: placeName$="CAPELLA":GOTO appendQuadrantNumber
9160 regionBetelgeuse: placeName$="BETELGEUSE":GOTO appendQuadrantNumber
9170 regionAldebaran: placeName$="ALDEBARAN":GOTO appendQuadrantNumber
9180 regionRegulus: placeName$="REGULUS":GOTO appendQuadrantNumber
9190 regionArcturus: placeName$="ARCTURUS":GOTO appendQuadrantNumber
9200 regionSpica: placeName$="SPICA"
9210 appendQuadrantNumber: IF regionNameOnly<>1 THEN ON nameQuadrantY GOTO suffixI,suffixII,suffixIII,suffixIV,suffixI,suffixII,suffixIII,suffixIV
9220 RETURN
9230 suffixI: placeName$=placeName$+" I":RETURN
9240 suffixII: placeName$=placeName$+" II":RETURN
9250 suffixIII: placeName$=placeName$+" III":RETURN
9260 suffixIV: placeName$=placeName$+" IV":RETURN
