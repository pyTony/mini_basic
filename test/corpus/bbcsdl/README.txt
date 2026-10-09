BBC BASIC for SDL 2.0 example corpus (plain-text sources).

mini_basic keeps only programs useful for a **general BASIC + pygame**
implementation (MODE/GCOL/PLOT/VDU, games, portable demos).

Kept categories:
  games/     animal, hanoi, sudoku, …
  graphics/  wheel, saucer, squares, fern, piechart, … (not OpenGL)
  general/   welcome, filters, poem, calculator, … (not network/WIMP)
  samples/   small tier-A fixtures

Removed (not in-tree; re-fetch skips these paths):
  tools/     TouchIDE, SDLIDE, compiler, mmap, …
  physics/   Box2D FN_b2* demos
  sounds/    multi-channel music / polly-class audio
  plus individual network/OpenGL demos (world, teapot, lighting, pyramid,
  bbcowl, Rubik, server, client, opengl, …)

Portable demos like **wheel** stay — they are ordinary BBC graphics, not
BBCSDL-only tooling.

Source index (upstream still hosts full tree):
  https://www.bbcbasic.co.uk/bbcsdl/examples/index.html

Refresh (skips tools/physics/sounds + known non-portable names):

  python test/manual/fetch_bbcsdl_corpus.py

Scan compatibility blockers:

  python -m mini_basic.bbcsdl_scan test/corpus/bbcsdl
