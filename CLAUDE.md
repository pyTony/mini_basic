# mini_basic notes for Claude

## Keyword case policy

- The **mini** dialect is not strict about keyword case: `for i = 1 to 2 : print i : next i`
  and `if x > 2 then print "big"` must work. Lowercase keywords are uppercased at entry;
  identifiers stay case-sensitive.
- Only the **bbc** dialect requires uppercase keywords (BBC BASIC tokenizes uppercase only).
  Do not make bbc accept lowercase keywords.
- Treat a lowercase-keyword failure in mini as a bug, not "by design".

## Tests

- Run `python -m pytest test -q -p no:cacheprovider`.
