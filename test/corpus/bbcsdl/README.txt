BBC BASIC for SDL 2.0 example corpus (plain-text sources).

Source index:
  https://www.bbcbasic.co.uk/bbcsdl/examples/index.html

Refresh the corpus:

  python test/manual/fetch_bbcsdl_corpus.py

Scan compatibility blockers:

  python -m mini_basic.bbcsdl_scan test/corpus/bbcsdl

Tests use mini_basic.bbcsdl_scan to rank programs by how close they are
to running in mini_basic today (tier A = Acorn-portable, D = OpenGL/SDL).