# Statement dispatch map

How a line of BASIC gets from the program store to the code that runs it.
Written for people and LLMs who need to find "where is X handled?" without
reading the 2,000-line `_execute_statement`. Names are functions or methods;
file paths are under `mini_basic/runtime_parts/` unless stated.

## 1. From text to stored line (once, at entry)

| Step | Where | What |
|------|-------|------|
| LOAD / typed line / EDIT | `program.py` `set_program_line` | Stores the line after `canonicalize_program_line` |
| Canonicalize | `program.py` `canonicalize_program_line` | Sanitize control chars; glue type suffixes (`A $`→`A$`); **mini**: uppercase lowercase keywords (`_fold_mini_keywords`); **bbc**: crunched keywords (`PRINTTAB`, `MODE5`, `DEFPROC…`, uppercase only, never after `@`); **mits/commodore/tiny**: `PRINTA`→`PRINT A`, `IFA=0THEN50` (`_space_crunched_ms_statements`); `1TO10` spacing; `?`→`PRINT`; monadic unglue (`TAN10`, `INKEY1`, `ASC"x"`) |
| Text encoding | `io.py` `_decode_program_text` | UTF-8, else CP1252 / Latin-1 (old sources) |
| Tokenized `.bbc` | `bbc_detokenize.py` | Detokenized to text, then the same path |

Design and phase status of "normalize once at entry": `docs/BBC_TOKENIZE_VS_UNGLUE.md`
(see §6 below for what still runs twice).

## 2. RUN loop

`core.py` `run` → `execution.py` `_run_program_loop` → `execute_line(line_num, text, line_nums)`
→ splits the line into statements (`program.py` `_parse_line_statements`, cached in
`_run_stmts`) → `_execute_statement` for each.

- A statement returns `None` (next statement), a line number (jump), or `-1` (stop).
- Same-line re-entry (FOR/REPEAT/WHILE bodies on one line, GOSUB returns) uses
  `self.resume_at = (line, statement_index)`.
- An IF … THEN clause runs as its own statement list via `_execute_inline_statements`
  (`_inline_exec_depth` > 0); GOSUB inside it records that list so RETURN resumes there.

Statement splitting (`core.py` `_split_colon_statements`): `:` outside strings, except
after `THEN` (the clause keeps its colons), after `REM` / a `'` comment (mini), in
`ON CLOSE|ERROR …` tails, and after `WHEN`/`OTHERWISE`. `name:` is a label only if `name`
is not a statement keyword (`_is_statement_keyword`, which includes the
keyword-prefixed heads below).

## 3. `_execute_statement` — the order of checks

`execution.py`. Each stage either handles the statement and returns, or falls through.

| # | Check | Handler |
|---|-------|---------|
| 1 | Empty or `;` | nothing |
| 2 | `REM …` / `' …` | comment. `' dialect: …` hint lines apply a dialect. **bbc**: `'` is *not* a comment → falls through to "Unknown statement" |
| 3 | Tail comment `X = 1 ' note` (not bbc) | `program.py` `_split_tail_apostrophe_comment` |
| 4 | `*command` | `_execute_star_command` (OSCLI, `*REFRESH`, …) |
| 5 | Plain numeric `LET`/`var = expr` | `_try_fast_numeric_assignment` (cached closure in `_stmt_fast_runners`) |
| 6 | First word in `_KEYWORD_PREFIXED_HEADS` (`ON OPTION RANDOMIZE CONT REPORT SWAP OPEN FIELD GET PUT LSET RSET CLOSE LINE`) | `_execute_keyword_prefixed`: ON MOUSE, ON CLOSE, ON ERROR LOCAL / inline / OFF / GOTO, OPTION BASE, RANDOMIZE, CONT, REPORT, SWAP, OPEN, FIELD, GET/PUT, LSET/RSET, CLOSE (not `CLOSE#`), LINE INPUT[#], ON … GOTO/GOSUB. Returns `MISSING` when none match |
| 7 | Inside DEF FN, `= expr` | FN return (`FnReturn`) |
| 8 | `@lib$…`, `IF @platform%…`, `SDL_SetWindowResizable` | BBCSDL setup stubs (ignored) |
| 9 | `_parse_command(line)` → `(cmd, rest)` | keyword recognition (case rules per dialect) |
| 10 | `cmd` in `_NOT_IMPLEMENTED_STATEMENTS` | "Out of scope" error |
| 11 | **dict dispatch** `stmt_simple.py` `dispatch_simple_stmt` | `REM INSTALL DATA OFF CLS CLG STOP OSCLI WAIT SOUND ENVELOPE TRACE TIMING LVAR WIDTH MOUSE KILL ERASE QUIT BYE GOODBYE` |
| 12 | `if cmd == …` chain (below) | the rest |
| 13 | fall through | "Unknown statement" |

Performance note: string comparisons in the chain cost ~0.5 µs to reach `IF`; the order
barely matters. Stage 6 used to run ~25 regexes on *every* statement (~10 µs); it is now
gated by the first word.

### The `if cmd ==` chain (stage 12), grouped

| Group | Commands (in chain order) | Notes |
|-------|---------------------------|-------|
| Output / input | `PRINT` (+`PRINT USING`), `BPUT#`, `PRINT#`, `WRITE`, `WRITE#`, `INPUT#`, `CLOSE#`, `INPUT` | PRINT items: `io.py` `_render_print_content` (bbc `@%` field, `'` newline, TAB/SPC) |
| Loops | `FOR`, `WHILE`, `NEXT`, `WEND`/`ENDWHILE`, `EXIT`, `BREAK`, `CONTINUE`, `REPEAT`, `UNTIL` | frames on `self.stack` (`LoopFrame`); FOR/WHILE have accelerators (`_try_accelerate_nested_int_fors`, `_try_accelerate_while_assign_body`) |
| Procedures | `PROC` (appears twice in the chain), `ENDPROC`, `DEF`, `LOCAL` | FN bodies/memo: `defs.py` |
| Jumps | `GOTO`, `GOSUB`, `RESUME`, `RETURN` | gosub entry = `(line, stmt, inline_parts, loop_depth)`; RETURN drops loop frames above `loop_depth` |
| CASE | `CASE`, `WHEN`, `OTHERWISE`, `ENDCASE` | layout cached per CASE line |
| IF | `IF`, `ELSEIF`, `ELSE`, `ENDIF` | block IF (`THEN` at line end) vs single-line IF; single-line: first `ELSE` splits (`core.py` `_split_if_else_parts`), nested IF in THEN gets the ELSE tail (`_then_code_with_nested_else`) |
| Assignment | `LET` **or any line containing `=`** | the default route for `A=1`, `A(I)=…`, `+=`, string assignment |
| Data | `DIM`, `READ`, `RESTORE` | DIM recompiles cached array reads (`_recompile_array_exprs`) |
| Misc | `ON` (bare) | |
| Graphics | `RECTANGLE`, `CIRCLE`, `MODE`, `GCOL`, `ORIGIN`, `MOVE`, `DRAW`, `LINE`, `PLOT`, `SPRITEDEF`, `SPRITE`, `VDU`, `COLOUR`/`COLOR` | `graphics.py`, `display.py` |
| Program | `CHAIN`, `RUN`, `END` | |

Known overlaps to keep in mind when changing things: `PROC` is tested twice; `LINE`
(graphics) vs `LINE INPUT` (stage 6); `ON …` forms are split between stage 6 and the
chain; `CLOSE` (stage 6) vs `CLOSE#` (chain); assignment is the fallback for any
statement containing `=`.

## 4. Expressions

| Need | Entry point | Path |
|------|-------------|------|
| Number | `expr.py` `_eval_numeric` / `eval_expr` | compiled cache `_get_compiled_expr` → Python code object (`expr/compile.py` `CompiledExpr`), else slow path `_eval_numeric_slow` (text substitution + eval) |
| Condition | `_eval_condition` | compiled condition, else boolean parser (`program.py` `_boolean_parse_*`, left-to-right chained comparisons) |
| String | `_eval_string_expr` / `_resolve_string_value` | cached plan (`strplan.py` `_get_string_plan`: `+` chains of literals, `A$`, `A$(i)`, `CHR$ STR$ LEFT$ RIGHT$ MID$ STRING$ SPACE$ UCASE$ LCASE$`), else the text resolver (expand calls to literals, split, resolve; BBC juxtaposition) |
| Type of an expression | `strplan.py` `_expr_static_kind` | the first operand decides (`LEN(A$)+1` is a number); `None` = unknown, old heuristics |
| PRINT item | `io.py` `_render_print_content` | string items vs numeric (`_is_string_print_item`; comparisons and `LEN(A$)+1`-style arithmetic are numeric) |

Compiled code: `expr/safe_eval.py` `compile_safe` validates the AST (no attribute access,
lambdas, comprehensions) and rewrites BASIC semantics (`MOD`/`DIV` truncate, `^`
left-associative). Math builtins compile to `math.*` (`__m_sin__` …); numeric array reads
to `__aget__(id, …)`; `LEN/ASC/VAL/INSTR` of a planned string to `__sfn__(id)`
(`_rewrite_string_calls_for_compile`). Variables are read from the live tables on every evaluation; only
the parse is cached.

## 5. Caches and when they are dropped

| Cache | Holds | Cleared by |
|-------|-------|-----------|
| `_run_stmts` | split statements per line | program change, RUN prepare |
| `_compiled_expr_cache` | `CompiledExpr` per source text | RUN / clear, dialect or CASE change, optimisation level; array readers recompiled on DIM |
| `_stmt_fast_runners` | fast LET/graphics closures | same as above |
| `_str_plan_cache`, `_static_kind_cache`, `__sfn__` thunks | string plans / expression kinds per text | with `_compiled_expr_cache` (`_clear_string_plan_caches`) |
| `_parse_command_cache` | `(cmd, rest)` per statement text (key = text only) | `_prepare_run` only — a dialect / CASE switch in the REPL applies to cached statements at the next RUN |
| FN memo | results of pure recursive DEF FN | RUN / redefinition |

## 6. Normalize-once status (double work)

Entry canonicalize (§1) is complete (Phase 1). The runtime copies of those rewrites were
**not removed**, because text that never passed entry still reaches the evaluator
(`EVAL("…")`, FN bodies built at runtime, immediate mode fragments). Instead each runtime
copy returns early when there is nothing left to rewrite:

| Runtime rewrite | Early return |
|-----------------|--------------|
| monadic unglue (`_unglue_monadic_expr`) | yes (Phase 2a) |
| operator normalize (`_normalize_operators`) | yes (2c) |
| bbc line glue in `_parse_command` | yes (2b) |
| `ASC"x"` unglue (`_unglue_asc_string_literal`) | yes (no `"` or no `ASC`) |
| bare `CHR$65` / `STR$~` expansion (`_expand_builtin_calls`) | yes (no `$` / `~` / name) |
| FOR `1TO10` spacing (`_normalize_for_rest`) | no — once per FOR execution, cheap |
| `?` → `PRINT` (`_expand_question_print`) | yes (first char test) |

Expression evaluation (not an entry rewrite, but the same "detect every form each time"
pattern): numeric expressions were already compiled once. String expressions now use a
cached plan (§4), and `LEN/ASC/VAL/INSTR` of a string stay inside compiled numeric code.
Forms the plan does not cover (juxtaposition, `""` literals, `STR$~`, `INKEY$`, FN
calls, …) still take the text path on every evaluation.

## 7. Adding a statement

1. Simple, no control flow: add `_h_name` to `stmt_simple.py` and register it in its
   dict. Handler returns `None` / line number / `-1`.
2. Needs a regex on the whole line before keyword parsing: add the first word to
   `_KEYWORD_PREFIXED_HEADS` and a branch in `_execute_keyword_prefixed`.
3. Otherwise: an `if cmd == 'NAME':` branch in `_execute_statement` near its group.
4. Keyword recognition: `runtime.py` `_STMT_KEYWORDS` (and the dialect keyword lists in
   `features/`); mini lowercase folding: `program.py` `_MINI_FOLD_STMT_WORDS`.
5. Tests: `test/test_edge_case_bugs.py` style (`_run(program_text, dialect)`).
