# Acceptance Criteria - Terminal Response Filter and Reconnect Recovery

Server-side patch of `TermSocket` in jupyter_server_terminals: filters terminal
query responses out of PTY output before they reach the browser, and after a
client attach forces a full app repaint via a PTY winsize bounce. One
consolidated doc for the plugin; tests live in
`jupyterlab_terminal_cpr_escape_fix/tests/test_handlers.py` (73 tests).

## Authors

- `@kj` Konrad Jelen

## Filter criteria `FILTER`

Terminal-to-shell responses that fish echoes as literal text on reconnect, each filtered in both ESC-prefixed and bare form (fish strips ESC from the introducer and the ST terminator)

- [x] `ACC-FILTER-1` **CPR filtered** - CRITICAL; `ESC[52;1R` stripped (`test_filters_cpr`)
  - evidence: `test_filters_cpr` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_cpr`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:31Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-2` **DA filtered** - HIGH; `ESC[?1;2c` stripped (`test_filters_da`)
  - evidence: `test_filters_da` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "test_filters_da and not da2"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:31Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-3` **DA2 filtered** - HIGH; `ESC[>0;276;0c` stripped (`test_filters_da2`)
  - evidence: `test_filters_da2` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_da2`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:31Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-4` **DECRPM filtered** - HIGH; `ESC[?12;2$y` stripped (`test_filters_decrpm`)
  - evidence: `test_filters_decrpm` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_decrpm`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:31Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-5` **OSC 10/11 filtered** - HIGH; `ESC]10;rgb:..ST` and `ESC]11;rgb:..ST` stripped (`test_filters_osc10`, `test_filters_osc11`)
  - evidence: `test_filters_osc10`, `test_filters_osc11` pass (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "test_filters_osc10 or test_filters_osc11"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:31Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-6` **Bare CPR filtered** - CRITICAL; `[2;1R` stripped (`test_filters_bare_cpr`)
  - evidence: `test_filters_bare_cpr` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_bare_cpr`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-7` **Bare DA filtered** - HIGH; `[?1;2c` stripped (`test_filters_bare_da`)
  - evidence: `test_filters_bare_da` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "test_filters_bare_da and not da2"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-8` **Bare DA2 filtered** - HIGH; `[>0;276;0c` stripped (`test_filters_bare_da2`)
  - evidence: `test_filters_bare_da2` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_bare_da2`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-9` **Bare DECRPM filtered** - HIGH; `[?12;2$y` stripped (`test_filters_bare_decrpm`)
  - evidence: `test_filters_bare_decrpm` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_bare_decrpm`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-10` **Bare OSC color filtered** - HIGH; `]10;rgb:..\` stripped (`test_filters_bare_osc_color_response`)
  - evidence: `test_filters_bare_osc_color_response` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_bare_osc_color_response`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-11` **Bare OSC multi filtered** - MEDIUM; two `]N;rgb:..\` in one chunk both stripped (`test_filters_multiple_bare_osc`)
  - evidence: `test_filters_multiple_bare_osc` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_multiple_bare_osc`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-12` **Bare OSC 4 palette filtered** - MEDIUM; `]4;1;rgb:..\` with palette index stripped (`test_filters_bare_osc4_palette`)
  - evidence: `test_filters_bare_osc4_palette` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_filters_bare_osc4_palette`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-13` **Full leaked prompt cleaned** - CRITICAL; the exact leaked byte mix reduces to `clear` (`test_bare_osc_full_leaked_prompt`)
  - evidence: `test_bare_osc_full_leaked_prompt` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bare_osc_full_leaked_prompt`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-FILTER-14` **Full fish response cleaned** - HIGH; all response types in one chunk fully stripped (`test_fish_shell_full_response`)
  - evidence: `test_fish_shell_full_response` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_fish_shell_full_response`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)

## Protection criteria `GUARD`

Genuine terminal output, shell-to-terminal queries and plain text that resembles a sequence pass through unchanged - the half that guards against over-filtering

- [x] `ACC-GUARD-15` **SGR colors preserved** - CRITICAL; `ESC[38;5;231m`, `ESC[38;2;..m`, `ESC[0m` untouched (`test_preserves_sgr_color_256`, `test_preserves_sgr_color_rgb`, `test_preserves_sgr_reset`)
  - evidence: 4 tests pass: `test_preserves_sgr_color_256`, `test_preserves_sgr_color_rgb`, `test_preserves_sgr_reset`, `test_preserves_color_codes` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "preserves_sgr or preserves_color_codes"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-16` **Cursor movement preserved** - CRITICAL; `ESC[5A/3B/71C/2D` untouched (4 tests)
  - evidence: 5 tests pass: `test_preserves_cursor_up`, `_down`, `_forward`, `_back`, `test_preserves_cursor_movement` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "preserves_cursor and not position"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-17` **Cursor position preserved** - CRITICAL; `ESC[10;20H` untouched (`test_preserves_cursor_position`)
  - evidence: `test_preserves_cursor_position` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_preserves_cursor_position`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-18` **Erase and scroll preserved** - HIGH; `ESC[K`, `ESC[2J`, `ESC[3S` untouched (3 tests)
  - evidence: 3 tests pass: `test_preserves_erase_line`, `test_preserves_erase_display`, `test_preserves_scroll_up` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "preserves_erase or preserves_scroll"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-19` **DEC private modes preserved** - HIGH; `ESC[?2004h`, `ESC[?1049h`, `ESC[?25h` untouched (3 tests)
  - evidence: 3 tests pass: `test_preserves_bracketed_paste_mode`, `test_preserves_alternate_screen`, `test_preserves_dec_private_mode_set` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "bracketed_paste or alternate_screen or dec_private_mode"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-20` **OSC 0/7/8/133 preserved** - MEDIUM; title, cwd, hyperlink, prompt mark untouched (4 tests)
  - evidence: 4 tests pass: `test_preserves_window_title_osc0`, `test_preserves_osc7_cwd`, `test_preserves_osc8_hyperlink`, `test_preserves_osc133_prompt_mark` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "osc0 or osc7 or osc8 or osc133"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-21` **OSC color queries preserved** - HIGH; `ESC]10;?`, `ESC]11;?`, `ESC]12;?` untouched (3 tests)
  - evidence: 3 tests pass: `test_preserves_osc10_query`, `test_preserves_osc11_query`, `test_preserves_osc12_query` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "osc10_query or osc11_query or osc12_query"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:32Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-22` **DA and DA2 queries preserved** - HIGH; `ESC[c`, `ESC[?c`, `ESC[>c`, `ESC[>0c` untouched (`test_preserves_da_query`, `test_preserves_da2_query`)
  - evidence: `test_preserves_da_query`, `test_preserves_da2_query` pass (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "preserves_da_query or preserves_da2_query"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-23` **OSC 52 clipboard preserved** - MEDIUM; BEL, ST, empty, primary, large payload variants untouched (5 tests)
  - evidence: 6 `osc52` tests pass, BEL, ST, empty, primary, large payload and mixed with a filtered OSC (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k osc52`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-24` **Plain bracket text preserved** - HIGH; `array[0]`, matrix, markdown link, git output, JSON brackets untouched (5 tests)
  - evidence: 5 tests pass: `test_preserves_array_index`, `test_preserves_matrix_notation`, `test_preserves_markdown_link`, `test_preserves_git_output`, `test_preserves_json_brackets` (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k "array_index or matrix_notation or markdown_link or git_output or json_brackets"`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-25` **Bare OSC needs rgb: payload** - HIGH; `note]10; and continue` untouched (`test_bare_osc_preserves_plain_text_close_bracket`)
  - evidence: `test_bare_osc_preserves_plain_text_close_bracket` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bare_osc_preserves_plain_text_close_bracket`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-26` **Bare OSC query preserved** - MEDIUM; `]11;?\` untouched (`test_bare_osc_preserves_bare_osc_query`)
  - evidence: `test_bare_osc_preserves_bare_osc_query` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bare_osc_preserves_bare_osc_query`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-27` **Bare OSC no double-count** - LOW; `ESC]10;rgb:..ST` counted once as `osc`, not again as `bare_osc` (`test_bare_osc_does_not_double_count_esc_prefixed`)
  - evidence: `test_bare_osc_does_not_double_count_esc_prefixed` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bare_osc_does_not_double_count_esc_prefixed`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-GUARD-49` **OSC 4 palette query preserved** - HIGH; live `ESC]4;1;?BEL` and `ESC]4;1;?ESC\` pass the output filter unchanged; the response `ESC]4;1;rgb:..ST` is still filtered
  - evidence: test_preserves_osc4_query_bel, test_preserves_osc4_query_st, test_filters_osc4_response_next_to_osc4_query pass; red with ESC_OSC reverted (logs/pytest-verify-mutation-esc-osc.log)
  - related: DEF-FILTER-8 - the defect this removes
  - blocked-by: ACC-REPLAY-41 - without the replay strip, OSC 4 queries would be answered on re-attach
  - test: `pytest -k "osc4_query or osc4_response"`
  - test-tags: UNIT
  - mechanism: 2026-09-24T14:20:34Z @kj `ESC_OSC` checks for `?` after the palette index: `\x1b\](?:4;\d+|1[0-2]);(?!\?)`
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T16:03:31Z @kj closed

## Toggle behaviour `TOGGLE`

Toggles live in `DEFAULTS` in `__init__.py` and are internal, not user settings

- [x] `ACC-TOGGLE-28` **Toggle: filter_osc_color_responses** - MEDIUM; True filters bare OSC color responses (default), False drops the `bare_osc` pattern before patching
  - evidence: True (default): 7 `bare_osc` tests pass (73/73 pytest green at 7cdea85, 2026-09-24); the False path has no test
  - test-tags: UNIT
  - test: `pytest -k bare_osc` for True; for False set `DEFAULTS['filter_osc_color_responses'] = False`, load the extension, assert no `bare_osc` entry in `FILTER_PATTERNS`
  - log: 2026-05-31T00:00:00Z @kj implemented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-TOGGLE-29` **Toggle: suppress_buffer_replay** - MEDIUM; False leaves the terminado replay intact (default), True silences `on_pty_read` during `open()`
  - evidence: True: `test_no_replay_open_suppresses_on_pty_read`, `test_on_pty_read_restored_after_open` pass (73/73 pytest green at 7cdea85, 2026-09-24); the False default has no test
  - test-tags: UNIT
  - test: `pytest -k TestBufferReplaySuppression`
  - log: 2026-05-31T00:00:00Z @kj documented (v1.0.10)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-TOGGLE-30` **Toggle: repaint_on_attach** - MEDIUM; True bounces PTY winsize after attach (default), False leaves reconnect behaviour untouched
  - evidence: True (default): `test_loader_wires_bounce_to_real_ptyproc` passes (73/73 pytest green at 7cdea85, 2026-09-24); the False path has no test
  - test-tags: UNIT
  - test: `pytest -k test_loader_wires_bounce_to_real_ptyproc`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)

## Repaint on attach `BOUNCE`

Full-screen repaint after a client attaches: the replay holds only diff frames, so a fresh client (window refresh) otherwise misses static regions such as the Claude Code status line and input box, which the live stream never redraws (observed 2026-08-13, `docs/observed-effects.md`)

- [x] `ACC-BOUNCE-31` **Bounce grows then restores** - HIGH; PTY set one row taller, original size restored one step later (`test_bounce_grows_then_restores`)
  - overridden-by: ACC-BOUNCE-68
  - mechanism: 2026-09-24T13:32:34Z @kj after the replay drains, `_make_winsize_bounce` sets the PTY one row taller and back; each size change makes the kernel send SIGWINCH and the foreground app repaints its full screen
  - evidence: `test_bounce_grows_then_restores` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bounce_grows_then_restores`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-32` **Settle delay** - MEDIUM; bounce fires 0.4 s after attach so client geometry is final
  - evidence: `_BOUNCE_DELAY = 0.4` in `__init__.py` at 7cdea85, read by hand on 2026-09-24; no test pins the value
  - test-tags: MANUAL
  - test: patch `IOLoop.call_later`, attach a `TermSocket`, assert the first scheduled delay is 0.4
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-33` **Debounce** - MEDIUM; at most one bounce per 5 s per terminal, so reconnect storms do not flicker-loop (`test_debounce_and_prune`)
  - evidence: `test_debounce_and_prune` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_debounce_and_prune`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12); test pin added after review
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-34` **Prune inert debounce entries** - LOW; entries aged past the debounce window are deleted in place on the next scheduled bounce, so `_last_bounce` stays bounded (`test_debounce_and_prune`)
  - evidence: `test_debounce_and_prune` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_debounce_and_prune`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-35` **Guarded restore** - HIGH; restore write skipped when the size changed mid-bounce, a racing real client resize is never clobbered (`test_bounce_restore_guarded_against_racing_resize`)
  - evidence: `test_bounce_restore_guarded_against_racing_resize` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bounce_restore_guarded_against_racing_resize`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-36` **Edge: no winsize support** - MEDIUM; terminal that cannot report its size is left untouched (`test_bounce_noop_when_getwinsize_fails`)
  - evidence: `test_bounce_noop_when_getwinsize_fails` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bounce_noop_when_getwinsize_fails`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:33Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-37` **Edge: grow write fails** - MEDIUM; failed grow schedules no restore (`test_bounce_noop_when_setwinsize_fails`)
  - evidence: `test_bounce_noop_when_setwinsize_fails` passes (73/73 pytest green at 7cdea85, 2026-09-24)
  - test-tags: UNIT
  - test: `pytest -k test_bounce_noop_when_setwinsize_fails`
  - log: 2026-08-13T00:00:00Z @kj implemented (v1.0.12)
  - log: 2026-09-24T13:32:34Z @kj edited importance and test (added) and test-tags (added) and evidence (added)
- [x] `ACC-BOUNCE-38` **Live verification** - CRITICAL; with the patch active, a window refresh leaves the Claude Code status line intact
  - evidence: owner observed on 2026-10-12 in the running lab (server process started 2026-10-09, package 1.0.15 installed): after a browser reload Claude Code's status line and input box are drawn again
  - test-tags: MANUAL
  - test: on a server running the patch, start Claude Code in a terminal, reload the browser tab, assert the status line and input box are drawn again
  - log: 2026-08-13T00:00:00Z @kj criterion added, pending make install + server restart
  - log: 2026-09-24T13:32:34Z @kj edited importance and test (added) and test-tags (added)
  - log: 2026-09-24T13:33:11Z @kj amended text "with the patch active, a window refresh leaves the Claude Code status line intact (requires `make install` and a server restart to load the patch; the installed copy predates the feature)" -> "with the patch active, a window refresh leaves the Claude Code status line intact"
  - log: 2026-09-24T13:33:14Z @kj installed copy in /opt/conda site-packages is 1.0.14 and has `_make_winsize_bounce`; whether the running lab server loaded it was not checked; still open until a refresh is observed on a patched server
  - log: 2026-10-12T10:29:21Z @kj closed
- [x] `ACC-BOUNCE-68` **Repaint step costs no line** - HIGH; the repaint step after an attach changes the PTY width by one column, never the row count; a program that addresses rows absolutely and commits a line during the step keeps every committed line and leaves no stale row
  - evidence: repaint-on-attach.spec.ts test 2 green in fish and bash, 3 of 3 trials; red on the row step (LOG55 missing, 5 LIVE rows, 3 of 3); TestWinsizeBounce 8 of 8, mutation m1 red; E5 0 of 10 damaged; logs/ui-tests-colstep-red-rows-8903.log, logs/verify-bounce-galata-fish-8904.log
  - related: DEF-BOUNCE-14 - the defect this step removes
  - overrides: ACC-BOUNCE-31
  - test: repaint-on-attach.spec.ts test 2: row-addressing stand-in under stress, 3 page reloads, every LOG line once and 4 LIVE rows; TestWinsizeBounce in tests/test_handlers.py
  - test-tags: FUNCTIONAL, UNIT
  - mechanism: 2026-10-12T13:30:32Z @kj setwinsize(rows, cols - 1) for 0.12 s then back; a row step made the program address one row below the browser's last row (E4, E5); narrower not wider because a PTY wider than the browser wraps a program that writes to the last column
  - log: 2026-10-12T13:30:32Z @kj added
  - log: 2026-10-12T14:04:43Z @kj closed
- [x] `ACC-BOUNCE-69` **No repaint step for a shell at its prompt** - HIGH; no repaint step while the terminal's foreground process group is one shell alone (bash, sh, dash, zsh, fish, ksh, tcsh, csh); a typed shell line that fills the width keeps the output above it; a shell with a child in its group is stepped; lookup error: step runs
  - evidence: repaint-on-attach.spec.ts test 3 green in fish and bash, red without the guard (marker count 0, own shell and nested bash); bug-hunter probe 0 of 7 damaged (was 7 of 7); sh -c and bash <script> programs repainted 3 of 3 each; TestWinsizeBounce 28 of 28; logs/review3-fix2-galata-fish-8901.log, logs/review3-fix-red-noguard-bash-8901.log
  - related: DEF-BOUNCE-17 - the defect this removes; ACC-BOUNCE-68 - the column step it guards
  - test: repaint-on-attach.spec.ts test 3: top-level shell and nested bash, typed line of cols-1, reconnect, three markers once each; TestWinsizeBounce guard cases
  - test-tags: FUNCTIONAL, UNIT
  - mechanism: 2026-10-12T15:44:59Z @kj _shell_at_prompt reads /proc/<tcgetpgrp(fd)>/comm and the leader's children file; a shell at its prompt needs no repaint, and a width step makes its line editor miscount the rows of a line that fills the width; a child in the leader's group means a program run without job control, which needs the repaint
  - log: 2026-10-12T14:47:28Z @kj added
  - log: 2026-10-12T15:44:59Z @kj amended title "No repaint step while a shell is in front" -> "No repaint step for a shell at its prompt"; text "the repaint step is skipped when the leader of the terminal's foreground process group is a shell (bash, sh, dash, zsh, fish, ksh, tcsh, csh); a shell prompt with a typed line that fills the width keeps the output above it across an attach; lookup error: the step runs" -> "HIGH; no repaint step while the terminal's foreground process group is one shell alone (bash, sh, dash, zsh, fish, ksh, tcsh, csh); a typed shell line that fills the width keeps the output above it; a shell with a child in its group is stepped; lookup error: step runs"
  - log: 2026-10-12T15:44:59Z @kj mechanism updated "2026-10-12T14:47:28Z @kj _shell_in_foreground reads /proc/<tcgetpgrp(fd)>/comm; a shell at its prompt needs no repaint because the replay restores its line, and a width step makes its line editor miscount the rows of a line that fills the width" -> "_shell_at_prompt reads /proc/<tcgetpgrp(fd)>/comm and the leader's children file; a shell at its prompt needs no repaint, and a width step makes its line editor miscount the rows of a line that fills the width; a child in the leader's group means a program run without job control, which needs the repaint"; reason: names both conditions of the guard and the reason for each
  - log: 2026-10-12T15:44:59Z @kj closed
- [-] `ACC-BOUNCE-70` **A defunct child does not count for the shell guard** - MEDIUM; a defunct child in the own process group of the shell does not count as a running program: the shell is taken as alone and gets no repaint step; a live child in the group still makes the step run; unreadable child state: step runs
  - related: ACC-BOUNCE-69 - the guard this refines; DEF-BOUNCE-20 - the defect this removes
  - test: TestWinsizeBounce guard cases: defunct child, live child, both, unreadable state; one test with real processes on a PTY
  - test-tags: UNIT
  - mechanism: 2026-10-13T17:06:33Z @kj `_shell_at_prompt` skips a child whose state field in /proc/<pid>/stat is Z
  - log: 2026-10-13T17:06:33Z @kj added
  - log: 2026-10-13T17:08:34Z @kj rejected: not adopted: DEF-BOUNCE-20 is rejected as a recorded limit with no change on screen; the guard rule stays as closed in ACC-BOUNCE-69

## Regression protection `SUITE`

Test rules that stop a filter change from stripping genuine output or regressing unnoticed

- [x] `ACC-SUITE-39` **New filter pattern ships with a protect test** - HIGH; a new `FILTER_PATTERNS` entry adds a filter test and at least one protect test proving its nearest legitimate look-alike survives; bare OSC: filters `]N;rgb:..\`, leaves plain `]10;` text and `]N;?` queries
  - evidence: `bare_osc`, added with the rule in v1.0.10, has 3 protect tests: `test_bare_osc_preserves_plain_text_close_bracket`, `test_bare_osc_preserves_bare_osc_query`, `test_bare_osc_does_not_double_count_esc_prefixed`; all pass (73/73 pytest green at 7cdea85, 2026-09-24)
  - test: for each `FILTER_PATTERNS` name added since the last release, find a filter test and a preserve test in `test_handlers.py` and run both with `pytest -k`
  - test-tags: UNIT
  - log: 2026-09-24T13:32:39Z @kj added
  - log: 2026-09-24T13:32:44Z @kj closed: carried over from the legacy Regression protection text; verified
- [x] `ACC-SUITE-40` **Full suite green before release** - CRITICAL; `python -m pytest jupyterlab_terminal_cpr_escape_fix/tests/` passes with 0 failures before a release; `make test` runs jest only, not pytest
  - evidence: `python -m pytest jupyterlab_terminal_cpr_escape_fix/tests/ -q`: 73 passed, 0 failed at 7cdea85 on 2026-09-24
  - test: `python -m pytest jupyterlab_terminal_cpr_escape_fix/tests/ -q`, assert 0 failed
  - test-tags: UNIT
  - log: 2026-09-24T13:32:39Z @kj added
  - log: 2026-09-24T13:32:44Z @kj closed: carried over from the legacy Regression protection text; verified
- [x] `ACC-SUITE-71` **A config file exception ends the test server** - LOW; an exception of ui-tests/jupyter_server_test_config.py ends the test server with an exit status that is not 0 and no listener: the build check and the switch check however the server is started, any other exception when Playwright starts the server
  - evidence: final tree, 2026-10-13: both checks by hand exit 1 in 1.6 to 1.7 s, 0 listeners (logs/cfgcheck-v2-hand-a-8905.log, cfgcheck-v2-hand-b-8905.log); value that is not JSON through Playwright exit 1 in 3.1 s, no new listener (cfgcheck-v2-playwright-badjson-8905.log); pytest 163, jest 11, lint, Galata 20 fish, 20 bash
  - related: DEF-SUITE-21 - the defect this removes
  - test: port 8905: by hand with an unknown CPR_FIX_DEFAULTS key, and with the package outside the working tree: exit status 1, no listener; through jlpm playwright test with a CPR_FIX_DEFAULTS value that is not JSON: exit status 1, no test server
  - test-tags: MANUAL
  - mechanism: 2026-10-13T17:59:48Z @kj the two checks raise SystemExit, which traitlets does not catch; ui-tests/playwright.config.js starts the server with TRAITLETS_APPLICATION_RAISE_CONFIG_FILE_ERROR=1, so traitlets raises every other exception of a config file
  - mechanism: 2026-10-13T17:06:36Z @kj the checks raise SystemExit, which the Jupyter config loader does not catch
  - log: 2026-10-13T17:06:36Z @kj added
  - log: 2026-10-13T17:59:48Z @kj amended title "A failed config check ends the test server" -> "A config file exception ends the test server"; text "when the build check or the switch check of ui-tests/jupyter_server_test_config.py fails, the server process ends with an exit status that is not 0 and binds no port" -> "LOW; an exception of ui-tests/jupyter_server_test_config.py ends the test server with an exit status that is not 0 and no listener: the build check and the switch check however the server is started, any other exception when Playwright starts the server"
  - log: 2026-10-13T17:59:48Z @kj edited test "start jupyter lab with the test config and an unknown CPR_FIX_DEFAULTS key on port 8905: exit status not 0, nothing listens on 8905" -> "port 8905: by hand with an unknown CPR_FIX_DEFAULTS key, and with the package outside the working tree: exit status 1, no listener; through jlpm playwright test with a CPR_FIX_DEFAULTS value that is not JSON: exit status 1, no test server"
  - log: 2026-10-13T17:59:53Z @kj closed

## Replay without queries `REPLAY`

Terminal queries are removed from the buffer replay of `TermSocket.open`, so an attaching client answers none; live output keeps its queries

- [x] `ACC-REPLAY-41` **Replay queries removed** - CRITICAL; the replay that `TermSocket.open` sends holds none of these, except a run of them that ends the replay (ACC-REPLAY-55): OSC `4;<n>;?`, `10;?`, `11;?`, `12;?` with BEL or ST, and the chained forms `4;<n>;?;<m>;?` and `10;?;?`; CSI `c`, `0c`, `>c`, `>0c`, `5n`, `6n`, `?6n`; DECRQM `?<n>$p` and `<n>$p`; DECRQSS `DCS $q..ST`
  - evidence: test_replay_query_removed 21 cases pass, 103 pytest green (logs/pytest-verify.log); 27 of 30 new tests red on HEAD (osc4_bel, osc4_st, osc4_multi pass there because HEAD ESC_OSC deleted OSC 4 queries)
  - related: DEF-REPLY-1 - the defect this removes
  - test: drive the loader over the real `TermSocket.open` with a fake terminal whose `read_buffer` holds one query per case; assert the `stdout` frame holds none (one case per listed form; BEL and ST each for the single forms, one terminator for each chained form)
  - test-tags: UNIT
  - mechanism: 2026-09-24T14:20:33Z @kj `_patched_open` sets `self.on_pty_read` to `strip_replay_queries` followed by the class `on_pty_read` for the duration of `_original_open`, then deletes it, the same shadowing `suppress_buffer_replay` uses
  - log: 2026-09-24T14:20:33Z @kj added
  - log: 2026-09-24T14:21:03Z @kj edited test "drive the loader over the real `TermSocket.open` with a fake terminal whose `read_buffer` holds one query per case; assert the `stdout` frame holds none (17 cases)" -> "drive the loader over the real `TermSocket.open` with a fake terminal whose `read_buffer` holds one query per case; assert the `stdout` frame holds none (one case per listed form, BEL and ST each)"
  - log: 2026-09-24T16:03:31Z @kj closed
  - log: 2026-09-24T16:22:23Z @kj amended text "the replay that `TermSocket.open` sends holds none of: OSC `4;<n>;?`, `10;?`, `11;?`, `12;?` with BEL or ST; CSI `c`, `0c`, `>c`, `>0c`, `5n`, `6n`, `?6n`; DECRQM `?<n>$p` and `<n>$p`; DECRQSS `DCS $q..ST`" -> "the replay that `TermSocket.open` sends holds none of these, except a run of them that ends the replay (ACC-REPLAY-55): OSC `4;<n>;?`, `10;?`, `11;?`, `12;?` with BEL or ST, and the chained forms `4;<n>;?;<m>;?` and `10;?;?`; CSI `c`, `0c`, `>c`, `>0c`, `5n`, `6n`, `?6n`; DECRQM `?<n>$p` and `<n>$p`; DECRQSS `DCS $q..ST`"
  - log: 2026-09-24T16:31:19Z @kj edited test "drive the loader over the real `TermSocket.open` with a fake terminal whose `read_buffer` holds one query per case; assert the `stdout` frame holds none (one case per listed form, BEL and ST each)" -> "drive the loader over the real `TermSocket.open` with a fake terminal whose `read_buffer` holds one query per case; assert the `stdout` frame holds none (one case per listed form; BEL and ST each for the single forms, one terminator for each chained form)"; evidence "test_replay_query_removed 19 cases pass, 101 pytest green (logs/pytest-verify.log); 26 of 28 new tests red on HEAD" -> "test_replay_query_removed 21 cases pass, 103 pytest green (logs/pytest-verify.log); 28 of 30 new tests red on HEAD"
  - log: 2026-09-24T16:36:18Z @kj edited evidence "test_replay_query_removed 21 cases pass, 103 pytest green (logs/pytest-verify.log); 28 of 30 new tests red on HEAD" -> "test_replay_query_removed 21 cases pass, 103 pytest green (logs/pytest-verify.log); 27 of 30 new tests red on HEAD (osc4_bel, osc4_st, osc4_multi pass there because HEAD ESC_OSC deleted OSC 4 queries)"
- [x] `ACC-REPLAY-42` **Live queries untouched** - CRITICAL; after open, a query in live PTY output reaches the client byte for byte, and with one client the program gets exactly one reply
  - evidence: test_live_query_after_open_unchanged and galata 'live query reaches the client unchanged and gets one reply' pass under fish and bash (logs/ui-tests-verify-fish.log, logs/ui-tests-verify-bash.log)
  - related: DEF-REPLY-1 - journal entry 12: deleting live queries broke negotiation
  - related: ACC-GUARD-21, ACC-GUARD-22 - the live query guards this extends to the replay path
  - test: unit: after the patched open, `TermSocket.on_pty_read(sock, '\x1b]11;?\x1b\\')` sends it unchanged; Galata: `ui-tests/tests/replay-queries.spec.ts` "live query reaches the client unchanged and gets one reply": OSC 11 query in stdout byte for byte, probe gets 1 reply, page sends 1 reply frame, fish command line empty (fish only)
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-09-24T14:20:33Z @kj added
  - log: 2026-09-24T14:52:43Z @kj edited test "unit: after the patched open, `TermSocket.on_pty_read(sock, '\x1b]11;?\x1b\\')` sends it unchanged; Galata: `research-replay-queries.spec.ts` baseline, probe count 1, command line empty" -> "unit: after the patched open, `TermSocket.on_pty_read(sock, '\x1b]11;?\x1b\\')` sends it unchanged; Galata: `ui-tests/tests/replay-queries.spec.ts` "live query reaches the client unchanged and gets one reply": OSC 11 query in stdout byte for byte, probe gets 1 reply, page sends 1 reply frame, fish command line empty (fish only)"
  - log: 2026-09-24T16:03:31Z @kj closed
- [x] `ACC-REPLAY-43` **Re-attach sends no replies** - CRITICAL; after 3 socket drops, 1 `session.reconnect()` and 3 page reloads, the server receives 0 reply-shaped `stdin` frames and fish's command line stays empty
  - evidence: galata '3 drops, 1 reconnect and 3 reloads send no replies' passes under fish and bash; red with strip off: 7 OSC 11 replies (logs/ui-tests-verify-mutation-strip-off-fish.log)
  - related: DEF-REPLY-1
  - test: `ui-tests/tests/replay-queries.spec.ts` "3 drops, 1 reconnect and 3 reloads send no replies": OSC 11 query in the replay; page sends 0 reply-shaped `stdin` frames; fish command line empty (fish only)
  - test-tags: FUNCTIONAL
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T14:52:43Z @kj edited test "`research-replay-queries.spec.ts` drop and reload tests asserting 0 `stdin` replies, an empty command line, and `printf 'ECHO_%s\n' X` printing `ECHO_X`" -> "`ui-tests/tests/replay-queries.spec.ts` "3 drops, 1 reconnect and 3 reloads send no replies": OSC 11 query in the replay; page sends 0 reply-shaped `stdin` frames; fish command line empty (fish only)"
  - log: 2026-09-24T16:03:31Z @kj closed
- [x] `ACC-REPLAY-44` **Edge: hidden tab opened earlier** - HIGH; a hidden terminal that was opened earlier and holds 3 OSC 11 queries in its replay sends 0 replies on re-attach
  - evidence: galata 'hidden terminal opened earlier sends no replies on re-attach' passes under fish and bash; red with strip off: 3 OSC 11 replies
  - related: DEF-REPLY-1 - the groups of three in the screenshot
  - test: `ui-tests/tests/replay-queries.spec.ts` "hidden terminal opened earlier sends no replies on re-attach": 3 OSC 11 queries, tab hidden and opened, socket drop; 0 reply-shaped `stdin` frames; fish command line empty (fish only)
  - test-tags: FUNCTIONAL
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T14:52:43Z @kj edited test "`research-replay-queries.spec.ts` three-hidden test asserting 0 `stdin` replies and an empty command line" -> "`ui-tests/tests/replay-queries.spec.ts` "hidden terminal opened earlier sends no replies on re-attach": 3 OSC 11 queries, tab hidden and opened, socket drop; 0 reply-shaped `stdin` frames; fish command line empty (fish only)"
  - log: 2026-09-24T16:03:31Z @kj closed
- [x] `ACC-REPLAY-45` **Edge: restored tabs never opened** - HIGH; with 2 terminals open, after one page reload the hidden terminal that was not opened since the reload sends no CSI or DCS replies
  - evidence: galata 'restored terminal never opened sends no CSI or DCS replies after reload' passes under fish and bash; red with strip off: 10 CSI/DCS replies
  - related: DEF-REPLY-1
  - test: `ui-tests/tests/replay-queries.spec.ts` "restored terminal never opened sends no CSI or DCS replies after reload": one terminal holds the 10 CSI and DCS queries, a second takes the tab, one reload; first terminal hidden and never opened; 0 reply-shaped `stdin` frames
  - test-tags: FUNCTIONAL
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T14:52:43Z @kj edited test "`research-replay-queries.spec.ts` inventory reload step asserting 0 `stdin` replies per terminal" -> "`ui-tests/tests/replay-queries.spec.ts` "restored terminal never opened sends no CSI or DCS replies after reload": one terminal holds the 10 CSI and DCS queries, a second takes the tab, one reload; first terminal hidden and never opened; 0 reply-shaped `stdin` frames"
  - log: 2026-09-24T16:03:31Z @kj closed
  - log: 2026-09-24T16:22:23Z @kj amended text "after one reload of 22 terminals, the hidden terminals that were never opened send no CSI or DCS replies" -> "with 2 terminals open, after one page reload the hidden terminal that was not opened since the reload sends no CSI or DCS replies"
- [x] `ACC-REPLAY-46` **Other replay bytes kept** - HIGH; stripping removes only query bytes; text, SGR, cursor movement, OSC 0/7/8/52/133 and responses in the buffer are unchanged
  - evidence: test_strip_keeps_responses and test_strip_removes_only_query_bytes pass, 101 pytest green
  - related: DEF-REPLY-1
  - test: unit: replay of mixed output with 3 queries; assert the result equals the input with exactly those 3 removed
  - test-tags: UNIT
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T16:03:31Z @kj closed
- [x] `ACC-REPLAY-47` **Edge: query cut at replay start** - LOW; a query tail left at the start of the replay after the deque dropped its head passes unchanged and raises nothing
  - evidence: test_query_tail_at_replay_start_kept passes, 101 pytest green
  - related: DEF-REPLY-1
  - test: unit: `read_buffer` starting `;?\x1b\\text`; assert the `stdout` frame equals it
  - test-tags: UNIT
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T16:03:31Z @kj closed
- [x] `ACC-REPLAY-48` **Toggle: strip_replay_queries** - MEDIUM; `DEFAULTS['strip_replay_queries']` True (default) strips queries from the replay; False sends the replay unchanged
  - evidence: test_strip_toggle_and_suppress_precedence passes; a mutant checking strip before suppress turns it red
  - related: DEF-REPLY-1
  - test: unit: load the extension with each value, replay `\x1b[c`, assert removed or kept
  - test-tags: UNIT
  - log: 2026-09-24T14:20:34Z @kj added
  - log: 2026-09-24T16:03:31Z @kj closed
- [x] `ACC-REPLAY-55` **Edge: trailing query kept** - HIGH; queries at the very end of the replay, with nothing printed after them, stay in the replay, so a program that queried while no client was attached and still waits gets its answer on attach
  - evidence: test_trailing_queries_kept passes; a mutant that drops the trailing run turns it red
  - related: DEF-REPLY-1 - keeps today's behaviour for a query that may still be awaited
  - test: unit: read_buffer ending in text then ESC[c; assert the stdout frame still ends in ESC[c; the same query followed by text is removed
  - test-tags: UNIT
  - log: 2026-09-24T14:25:01Z @kj added
  - log: 2026-09-24T16:03:31Z @kj closed

## Fitted terminal size `WIDTH`

A terminal widget sends its size to the PTY and parses PTY output only at its fitted xterm size; frontend `src/index.ts`, needs a rebuild

- [x] `ACC-WIDTH-50` **No set_size before fit** - HIGH; a widget whose xterm was never opened sends no `set_size`, so a hidden restored tab never resizes its PTY to 24x80
  - evidence: Galata `background-terminal.spec.ts` test a: no `set_size` [24, 80] frame for the hidden terminal after a reload, at least one frame once shown, fish and bash; jest: held `set_size`, passed `stdin`, passed `set_size` right after the open; 10 of 10 jest, 10 of 10 Galata per shell
  - related: DEF-WIDTH-4 - the defect this removes
  - test: Galata `background-terminal.spec.ts`: after a reload no `set_size` frame with rows 24 and cols 80 is sent for the hidden terminal, and at least one frame is sent once it is shown
  - test-tags: UNIT, FUNCTIONAL
  - mechanism: 2026-10-12T06:27:03Z @kj the plugin wraps `session.send` of each widget from `ITerminalTracker.widgetAdded` until the widget node holds an element with class `xterm`; a `set_size` sent before that is not passed on; the fit after the open sends the real size
  - mechanism: 2026-09-24T14:20:35Z @kj `src/index.ts` patches `Terminal.prototype._setSessionSize` from the shared `@jupyterlab/terminal` to return while `_termOpened` is false; the first fit after show sends the size
  - log: 2026-09-24T14:20:35Z @kj added
  - log: 2026-09-24T14:24:53Z @kj rejected: dropped: frontend fix in JupyterLab @jupyterlab/terminal, not in this extension; see DEF-WIDTH-3
  - log: 2026-10-12T06:27:03Z @kj reopened: reopened: joins the DEF-WIDTH-3 fix after experiment E3
  - log: 2026-10-12T06:27:03Z @kj mechanism overridden; reason: public API route replaces the private `_setSessionSize` patch
  - log: 2026-10-12T06:27:04Z @kj edited test "`research-fish-width.spec.ts` T5 asserting no `set_size` [24, 80] and no `setwinsize` 24x80 for terminal A while hidden" -> "Galata `background-terminal.spec.ts`: after a reload no `set_size` frame with rows 24 and cols 80 is sent for the hidden terminal, and at least one frame is sent once it is shown"; test-tags "FUNCTIONAL" -> "UNIT, FUNCTIONAL"
  - log: 2026-10-12T08:21:36Z @kj closed
- [x] `ACC-WIDTH-51` **Replay parsed at fitted size** - HIGH; a background tab restored by a reload shows its history laid out at its fitted size once it is shown: a block drawn with cursor movement appears once
  - evidence: Galata `background-terminal.spec.ts` test a: each of 4 markers once and 2 websocket opens after the background tab is shown, fish and bash (markers [2, 2, 1, 1] and 1 open on 1.0.15); E3 on build 1.0.16: 0 duplicated markers in 2 of 2 runs
  - related: DEF-WIDTH-3 - the defect this removes
  - test: Galata `background-terminal.spec.ts`: a block drawn twice with a cursor-up shows each marker once after the background tab is shown (2 of 4 markers twice before the fix); 2 websocket opens after the reload
  - test-tags: UNIT, FUNCTIONAL
  - mechanism: 2026-10-12T10:36:03Z @kj when the widget node first holds an element with class `xterm` and a stdout message arrived while the tab was hidden, the plugin calls public `ITerminal.refresh()` once; the server replays the history into the fitted xterm
  - mechanism: 2026-10-12T06:27:04Z @kj when the widget node first holds an element with class `xterm` and a stdout message arrived before, the plugin calls public `ITerminal.refresh()` once; the server replays the history into the fitted xterm
  - mechanism: 2026-09-24T14:20:35Z @kj a widget first opened after it received stdout resets its xterm and calls `session.reconnect()`, so the server replays into the fitted xterm and the bounce repaints TUIs at that size
  - log: 2026-09-24T14:20:35Z @kj added
  - log: 2026-09-24T14:24:53Z @kj rejected: dropped: frontend fix in JupyterLab @jupyterlab/terminal, not in this extension; see DEF-WIDTH-3
  - log: 2026-10-12T05:32:28Z @kj reopened: reopened: fix for DEF-WIDTH-3 requested 2026-10-12
  - log: 2026-10-12T06:27:04Z @kj mechanism overridden; reason: public `refresh()` replaces the xterm reset, which needs the private `_term`
  - log: 2026-10-12T06:27:04Z @kj edited test "`research-fish-width.spec.ts` T5 `e-terminal-a-shown` asserting 0 right-only prompt rows (40 today)" -> "Galata `background-terminal.spec.ts`: a block drawn twice with a cursor-up shows each marker once after the background tab is shown (2 of 4 markers twice before the fix); 2 websocket opens after the reload"; test-tags "FUNCTIONAL" -> "UNIT, FUNCTIONAL"
  - log: 2026-10-12T06:27:04Z @kj amended text "a background tab restored by a reload shows its history parsed at its fitted size: once shown it has 0 stacked right-prompt rows" -> "HIGH; a background tab restored by a reload shows its history laid out at its fitted size once it is shown: a block drawn with cursor movement appears once"
  - log: 2026-10-12T08:21:36Z @kj closed
  - log: 2026-10-12T10:36:03Z @kj mechanism overridden; reason: trigger narrowed from any stdout before the open to stdout received while hidden (DEF-WIDTH-16)
- [-] `ACC-WIDTH-52` **set_size on every connect** - HIGH; after a socket drop or `session.reconnect()` the widget sends `set_size` with its fitted size, and the PTY follows the narrowest attached client
  - related: DEF-WIDTH-5 - the defect this removes
  - test: `research-fish-width.spec.ts` T3 `g-narrow-typed-after-drop` asserting `set_size` 63x77 after the reconnect open and 0 new stacked rows (38 today)
  - test-tags: FUNCTIONAL
  - mechanism: 2026-09-24T14:20:35Z @kj `_initialConnection` stays connected to `connectionStatusChanged`; on each later `connected`, which fires on `setup` before the replay, it resets the xterm and sends `set_size` if opened
  - log: 2026-09-24T14:20:35Z @kj added
  - log: 2026-09-24T14:24:53Z @kj rejected: dropped: frontend fix in JupyterLab @jupyterlab/terminal, not in this extension; see DEF-WIDTH-3
- [-] `ACC-WIDTH-53` **Edge: lab restart** - MEDIUM; after a server stop and start, the old page's reconnected widget sets the new shell's PTY to its xterm size
  - related: DEF-WIDTH-5
  - test: `research-fish-width.spec.ts` T2 `c-after-recreate-before-reload` asserting `setwinsize` 63x177 after the reconnect open (24x80 today)
  - test-tags: FUNCTIONAL
  - log: 2026-09-24T14:20:35Z @kj added
  - log: 2026-09-24T14:24:53Z @kj rejected: dropped: frontend fix in JupyterLab @jupyterlab/terminal, not in this extension; see DEF-WIDTH-3
- [x] `ACC-WIDTH-54` **Reconnect keeps one copy of history** - MEDIUM; the server clears the client's terminal before every replay (switch clear_before_replay), so the buffer holds the history once after a reconnect, and a new shell that attaches before its first output starts on an empty screen
  - evidence: Galata c: history once after a reconnect, red on cf2b773 (markers [2,2,2,2]); probe P2: lines and cursor identical across a reconnect; restarted shell: clear sent on an empty replay, pytest test_empty_buffer_still_clears, no end-to-end test (client disposes on disconnect)
  - mechanism: 2026-10-12T11:58:57Z @kj the server puts a clear sequence in front of the replay that TermSocket.open sends (switch clear_before_replay), so the client's kept xterm is emptied before the history is written
  - related: DEF-WIDTH-7 - the defect this removes
  - test: replay-clear.spec.ts test c: each history marker once after reconnectTerminal; pytest test_empty_buffer_still_clears for the empty replay
  - test-tags: FUNCTIONAL
  - log: 2026-09-24T14:20:35Z @kj added
  - log: 2026-09-24T14:24:53Z @kj rejected: dropped: frontend fix in JupyterLab @jupyterlab/terminal, not in this extension; see DEF-WIDTH-3
  - log: 2026-10-12T11:58:57Z @kj reopened: reopened: owner ordered a server-side clear before each replay on 2026-10-12; the criterion no longer needs a JupyterLab change
  - log: 2026-10-12T13:30:53Z @kj closed
  - log: 2026-10-12T14:46:58Z @kj amended text "the xterm is reset before a reconnect's replay, so its buffer holds the history once and a restarted shell starts on a clean screen" -> "MEDIUM; the server clears the client's terminal before every replay (switch clear_before_replay), so the buffer holds the history once after a reconnect, and a new shell that attaches before its first output starts on an empty screen"
  - log: 2026-10-12T14:46:58Z @kj edited test "`research-fish-width.spec.ts` T3 `f-narrow-reconnected` asserting left-prompt rows equal `e-narrow-attached` (16 against 8 today)" -> "replay-clear.spec.ts test c: each history marker once after reconnectTerminal; pytest test_empty_buffer_still_clears for the empty replay"
- [x] `ACC-WIDTH-56` **Setting turns the redraw off** - HIGH; the Settings Editor lists the background-tab redraw under this extension, on by default; with it off a background tab is not refreshed when first shown
  - evidence: Settings Editor lists the checkbox "Redraw background terminals when first shown", ticked by default (`logs/ui-tests-settings-editor-8901.log`); Galata test b: 1 websocket open with the setting off, 2 with it on; jest: nothing held back or refreshed when `isEnabled` is false
  - related: DEF-WIDTH-3 - the fix this switch controls
  - test: Galata: with the setting off, show a background terminal after a reload and assert no second websocket opens for it
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-10-12T05:32:28Z @kj added
  - log: 2026-10-12T08:21:36Z @kj closed
- [x] `ACC-WIDTH-57` **Visible terminal is not reconnected** - HIGH; a terminal that is visible when its output arrives, a new one included, keeps 1 websocket open; only output received while the tab is hidden leads to the redraw
  - evidence: Galata `a terminal the user creates is not reconnected`: 1 websocket open, 4 of 4 with bare bash on build 1.0.17 (2 opens in 4 of 4 on 1.0.16); suite 11 of 11 in fish and bash; jest case for output received while visible
  - related: DEF-WIDTH-16 - the defect this removes
  - test: Galata `background-terminal.spec.ts`: a terminal created with `terminal:create-new` on a fresh page has 1 websocket open; discriminates with bash, whose prompt arrives before the xterm module has loaded
  - test-tags: UNIT, FUNCTIONAL
  - mechanism: 2026-10-12T10:36:03Z @kj `holdUntilOpened` counts a stdout message only while `terminal.isVisible` is false
  - log: 2026-10-12T10:36:03Z @kj added
  - log: 2026-10-12T10:43:59Z @kj closed

## Clear before replay `CLEAR`

The server empties the client's terminal before each history replay

- [x] `ACC-CLEAR-58` **Replay starts on an empty terminal** - HIGH; the replay that TermSocket.open sends starts with cursor home, erase screen and erase scrollback; the replayed bytes after it are unchanged and the response filter leaves the prefix intact
  - evidence: pytest test_prefix_present_replay_bytes_unchanged, test_response_filter_leaves_prefix_intact, test_empty_buffer_still_clears; Galata first-frame test: replay frame starts ESC[H ESC[2J ESC[3J; mutations m1, m3, m10 red; logs/pytest-fixlist.log, logs/ui-tests-fixlist-fish-8901.log
  - test: pytest for clear_before_replay and for the patched open with a fake socket
  - test-tags: UNIT
  - mechanism: 2026-10-12T11:58:57Z @kj pure function clear_before_replay(text) in its own module, applied to the replay only, after query stripping
  - log: 2026-10-12T11:58:57Z @kj added
  - log: 2026-10-12T13:30:42Z @kj closed
- [x] `ACC-CLEAR-59` **Edge: alternate screen inside the replay** - HIGH; first alternate-screen switch in the replay is an entry: the prefix leaves the alternate screen and clears the normal one; first switch is a leave: the prefix clears the normal screen, then enters the alternate screen
  - evidence: pytest entry and leave cases for 47, 1047, 1049 and parameter lists (m2, m8 red); Galata b (entry) and f (leave: no alternate-screen row on the normal screen after exit and reconnect) green in fish and bash, red with the switch off; logs/ui-tests-canary-clear-fixlist-8903.log
  - test: pytest, one case per branch, modes 47, 1047, 1049 and a parameter list
  - test-tags: UNIT
  - log: 2026-10-12T11:58:57Z @kj added
  - log: 2026-10-12T13:30:42Z @kj closed
- [x] `ACC-CLEAR-60` **Edge: alternate screen older than the replay** - HIGH; a replay with no alternate-screen switch does not change which screen the client shows; a full-screen program whose start is older than the replay stays on the alternate screen across a reconnect
  - evidence: pytest test_no_switch_clears_only; Galata d: buffer alternate after 1600 chunks and a reconnect, replay holds no ESC[?1049h; m2 and m3 red; content older than the replay returns through repaint_on_attach (repaint-on-attach.spec.ts test 1); logs/ui-tests-fixlist-fish-8901.log
  - test: pytest for the branch; Galata: stand-in in alt mode, more than 1000 chunks, plain reconnect, buffer type still alternate
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-10-12T11:58:57Z @kj added
  - log: 2026-10-12T13:30:43Z @kj closed
- [x] `ACC-CLEAR-61` **Input modes survive a reconnect** - HIGH; the prefix resets no terminal mode: bracketed paste and mouse reporting that a program set before a reconnect are still set after it
  - evidence: Galata d: mouse vt200 and bracketedPasteMode true after the reconnect with no mode in the replay; m3 (ESC c) turns d red; pytest test_prefix_resets_no_input_mode; logs/ui-tests-fixlist-fish-8901.log, logs/ui-tests-verify-clear-m3-8904.log
  - test: Galata: set modes 2004 and 1000, plain reconnect, read term.modes; pytest: the prefix is one of three fixed strings
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-10-12T11:58:57Z @kj added
  - log: 2026-10-12T13:30:43Z @kj closed
- [x] `ACC-CLEAR-62` **Redraw first row clean** - MEDIUM; after the background-tab redraw the first buffer row is the first replayed line, not the old cursor row
  - evidence: Galata a green in fish and bash, red on cf2b773 in fish (row 0 joined to prompt text) and in the canary run; in bash a passes without the fix, stated in the spec header; logs/ui-tests-clear-red-8901.log, logs/ui-tests-canary-clear-fixlist-8903.log
  - related: DEF-WIDTH-12
  - test: Galata: background terminal, reload, show the tab, compare buffer row 0 with the first line of the history
  - test-tags: FUNCTIONAL
  - log: 2026-10-12T11:59:08Z @kj added
  - log: 2026-10-12T13:30:43Z @kj closed
- [x] `ACC-CLEAR-63` **History before a full-screen program redrawn** - MEDIUM; in a background tab whose program entered the alternate screen within the replay, the lines printed before that program have the fitted layout after the redraw and after the program exits
  - evidence: Galata b green in fish and bash, red on cf2b773 (markers [2,2,1,1]) and with the switch off; logs/ui-tests-clear-red-8901.log, logs/ui-tests-canary-clear-fixlist-8903.log
  - related: DEF-WIDTH-13
  - test: Galata: marker block, stand-in in alt mode, reload in background, show the tab, exit the stand-in, markers once per row
  - test-tags: FUNCTIONAL
  - log: 2026-10-12T11:59:08Z @kj added
  - log: 2026-10-12T13:30:43Z @kj closed
- [x] `ACC-CLEAR-64` **Toggle: clear_before_replay** - MEDIUM; DEFAULTS['clear_before_replay'] True (default) puts the prefix in front of the replay; False sends the replay as before; suppress_buffer_replay still takes precedence
  - evidence: pytest test_default_is_on, test_switch_off_replay_is_unchanged, test_nothing_sent_under_suppress_buffer_replay, test_empty_buffer_switch_off_sends_nothing; Galata first-frame test with the switch off: no prefix; logs/pytest-fixlist.log, logs/ui-tests-clear-off-skip-8901.log
  - test: pytest for both values; Galata run with CPR_FIX_DEFAULTS clear_before_replay false: first stdout frame after open has no prefix
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-10-12T11:59:08Z @kj added
  - log: 2026-10-12T13:30:43Z @kj closed

## Monkey patch ledger `PATCH`

Every replaced upstream attribute is listed, switchable and removable

- [x] `ACC-PATCH-65` **Ledger lists every monkey patch** - HIGH; README section and docs/monkeypatches.md list each replaced upstream attribute and each feature on it: target, switch, canary test, retire condition, removal steps, upstream versions last checked
  - evidence: README table MP-1 to MP-6 and docs/monkeypatches.md name every assignment site (TermSocket.on_pty_read, TermSocket.open, instance on_pty_read, session.send in src/unopenedTerminal.ts) with switch, canary, retire condition, removal steps and served versions 4.6.4, 7.6.4, xterm 5.5.0; verifier's register errors corrected
  - test: compare the register with every assignment to TermSocket attributes in the Python package and to session.send in src/
  - test-tags: MANUAL
  - log: 2026-10-12T11:59:09Z @kj added
  - log: 2026-10-12T13:30:53Z @kj closed
- [x] `ACC-PATCH-66` **Canary shows a patch is still needed** - HIGH; each register entry names a test that fails with the entry's switch off, or states that none exists; a canary that passes with the switch off means upstream no longer needs the patch
  - evidence: canaries red with the switch off: MP-3 replay-queries tests 2 to 4, MP-4 replay-clear a, b, c, f, MP-5 repaint-on-attach test 1, MP-6 background-terminal test 1 on upstream assertions only; MP-1 and MP-2 state none; logs/ui-tests-canary-*-fixlist-8903.log
  - test: run each named canary with its switch off; record pass or fail per entry
  - test-tags: FUNCTIONAL, MANUAL
  - log: 2026-10-12T11:59:09Z @kj added
  - log: 2026-10-12T13:30:53Z @kj closed
- [x] `ACC-PATCH-67` **Clear before replay removable as a unit** - MEDIUM; following the register's removal steps for clear_before_replay on a copy of the package (module, import, call, DEFAULTS key, its tests) leaves the remaining pytest suite green
  - evidence: removal drill repeated on the final code (tmp/research/review3/removal-drill-r1.py): steps 1 to 4 leave __init__.py and test_handlers.py equal to cf2b773 apart from the repaint step changes (2 hunks, 5 hunks in TestWinsizeBounce), no reference left, pytest 125 of 125; logs/review3-fix2-removal-drill.log
  - test: removal drill on a scratch copy, then pytest
  - test-tags: MANUAL
  - log: 2026-10-12T11:59:09Z @kj added
  - log: 2026-10-12T13:30:53Z @kj closed
  - log: 2026-10-12T15:44:59Z @kj edited evidence "removal drill on a scratch copy by implementer and verifier: steps 1 to 4 reproduce HEAD's __init__.py and test_handlers.py exactly, no reference left, pytest 103 of 103; logs/pytest-removal-drill.log, logs/pytest-verify-removal-drill.log" -> "removal drill repeated on the final code (tmp/research/review3/removal-drill-r1.py): steps 1 to 4 leave __init__.py and test_handlers.py equal to cf2b773 apart from the repaint step changes (2 hunks, 5 hunks in TestWinsizeBounce), no reference left, pytest 125 of 125; logs/review3-fix2-removal-drill.log"

