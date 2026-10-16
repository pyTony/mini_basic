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

## Agent TODOs

- [ ] Duplicate function `_parse_path_arg`
- [ ] Duplicate function `_apply_pygame_display_defaults`
- [ ] Missing tests for bbc_mode_spec
- [ ] Missing tests for amplitude_to_volume
- [ ] Missing tests for teletext_mosaic_pattern
- [ ] Missing tests for near_equal
- [ ] Missing tests for basic_truth
- [ ] Missing tests for safe_eval
- [ ] Missing tests for glyph_rows
- [ ] Missing tests for detect_bbc_binary_format
- [ ] Missing tests for map_mode_text_colour
- [ ] Missing tests for detokenize_line_body
- [ ] Missing tests for bbc_os_scales
- [x] Missing tests for parse_wilson_program
- [x] Missing tests for basic_error_wording
