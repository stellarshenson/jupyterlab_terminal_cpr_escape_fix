# Defects - Terminal Response Filter and Reconnect Recovery

Observed wrong behaviour on the terminal path - the `TermSocket` patch, terminado's replay and the JupyterLab terminal widget - with the trail of what was tried against each.

## Authors

- `@kj` Konrad Jelen

## Replay replies `REPLY`

Terminal answers from xterm.js that reach the PTY as stdin and that fish inserts as typed text

- [x] `DEF-REPLY-1` **Old queries answered again on every re-attach** - MAJOR; after a return to the lab fish's command line holds `]11;rgb:2525/2b2b/3232\` three times per re-attach and Enter prints `fish: Unknown command`; cause: `TermSocket.open` replays old queries and every attaching xterm answers them; fix: strip queries from the replay; `handlers.py`, `__init__.py`
  - evidence: strip_replay_queries on the TermSocket.open replay; replay-queries.spec.ts 4 of 4 green under fish and bash, 3 red with strip off; 103 pytest green; live lab needs make install and a server restart
  - related: ACC-REPLAY-41 - the fix criterion
  - attachment: ../paste-20260924-140505.png sha256:5bc136c85ddf8f41 edited:2026-09-24T12:05:06Z
  - repro: a program in fish sends `ESC]11;?ESC\` and reads the reply; reload the page; fish's command line holds `]11;rgb:..\` (`ui-tests/tests/replay-queries.spec.ts` test "3 drops, 1 reconnect and 3 reloads send no replies")
  - test-tags: UNIT, FUNCTIONAL
  - root-cause: 2026-09-24T14:18:34Z @kj terminado `TermSocket.open` sends the joined `read_buffer`, old queries included, to each new socket; xterm.js answers each query via `onData`; the lab sends each answer as `stdin`; fish 3.7 drops the ESC and inserts the rest; proven in E1 S2-S5 with filter and bounce on or off
  - log: 2026-09-24T14:18:34Z @kj added
  - log: 2026-09-24T14:18:42Z @kj reported: screenshot `paste-20260924-140505.png`, terminal 4 after the 14:02 re-attach of 7 terminals; its replay holds 3 `ESC]11;?ESC\` queries from `download-images.py`; filter log 225 `bare_osc` hits at 14:03:40
  - log: 2026-09-24T14:18:42Z @kj attached ../paste-20260924-140505.png sha256:5bc136c85ddf8f41
  - log: 2026-09-24T14:18:55Z @kj the clock times in the reported line are CEST (UTC+2) from /var/log/jupyterlab.log: 14:02 is 2026-09-24T12:02Z
  - log: 2026-09-24T16:03:32Z @kj closed
  - log: 2026-09-24T16:22:23Z @kj amended text "after a return to the lab fish's command line holds `]11;rgb:2525/2b2b/3232\` three times per re-attach and Enter prints `fish: Unknown command`; cause: `TermSocket.open` replays old queries and every attaching xterm answers them; fix: strip queries from the replay; `__init__.py`" -> "after a return to the lab fish's command line holds `]11;rgb:2525/2b2b/3232\` three times per re-attach and Enter prints `fish: Unknown command`; cause: `TermSocket.open` replays old queries and every attaching xterm answers them; fix: strip queries from the replay; `handlers.py`, `__init__.py`"
  - log: 2026-09-24T16:22:23Z @kj edited repro "a program in fish sends `ESC]11;?ESC\` and reads the reply; reload the page; fish's command line holds `]11;rgb:..\` (`research-replay-queries.spec.ts` drop and reload tests)" -> "a program in fish sends `ESC]11;?ESC\` and reads the reply; reload the page; fish's command line holds `]11;rgb:..\` (`ui-tests/tests/replay-queries.spec.ts` test "3 drops, 1 reconnect and 3 reloads send no replies")"
  - log: 2026-09-24T16:36:18Z @kj edited evidence "strip_replay_queries on the TermSocket.open replay; replay-queries.spec.ts 4 of 4 green under fish and bash, 3 red with strip off; 101 pytest green; live lab needs make install and a server restart" -> "strip_replay_queries on the TermSocket.open replay; replay-queries.spec.ts 4 of 4 green under fish and bash, 3 red with strip off; 103 pytest green; live lab needs make install and a server restart"
- [-] `DEF-REPLY-2` **Every attached client answers a live query** - MEDIUM; with 2 clients on one terminal a live `ESC]11;?ESC\` gets 2 replies and the second lands in fish as `]11;rgb:..\`; cause: every opened xterm answers and terminado forwards stdin from every client; fix: decision pending, needs a per-client stdin rule; `__init__.py`
  - repro: open one terminal in two split panes; a program sends `ESC]11;?ESC\` and reads one reply; fish's command line holds `]11;rgb:..\`
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:34Z @kj each opened xterm attached to the terminal answers the query, so N clients send N `stdin` replies; a program that reads one reply leaves N-1 for the shell, one that reads until 0.3 s of silence consumes all; proven in E1 S10
  - log: 2026-09-24T14:18:34Z @kj added
  - log: 2026-09-24T14:18:42Z @kj found by the `research-replay-queries.spec.ts` multi test; not tied to the screenshot
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix: needs a new per-client rule on stdin that can drop real replies; only with two clients on one terminal

## Terminal width `WIDTH`

fish right-prompt rows stack when output rendered for one PTY width is parsed by a narrower xterm

- [-] `DEF-WIDTH-3` **Background tab parses its replay at 80x24** - MEDIUM; after a page reload a background fish tab, once shown, has dozens of stacked right-prompt rows; cause: JupyterLab `Terminal._onMessage` writes the replay into an xterm not yet opened or fitted, at 80x24; owner JupyterLab; fix: on first open after stdout, reset the xterm and reconnect; `src/index.ts`
  - related: ACC-WIDTH-51 - the fix criterion
  - attachment: ../paste-20260924-140505.png sha256:5bc136c85ddf8f41 edited:2026-09-24T12:05:06Z
  - repro: fish tabs A and B; 2 commands in A; activate B; reload the page; activate A: stacked right-prompt rows
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj `onUpdateRequest` opens and fits the xterm only when the widget is visible, `_onMessage` writes stdout at once, so a hidden tab wraps its replay at 80 columns and the widening reflow keeps the wraps; proven in E2 T5 (40 stacked rows after fit) and T4 (screenshot reproduced row for row)
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj reported: stacked `main !5 ?1 | 13s` rows in screenshot `paste-20260924-140505.png`; likely a page reload at 14:02, not confirmed
  - log: 2026-09-24T14:18:43Z @kj attached ../paste-20260924-140505.png sha256:5bc136c85ddf8f41
  - log: 2026-09-24T14:18:55Z @kj the clock times in the reported line are CEST (UTC+2) from /var/log/jupyterlab.log: 14:02 is 2026-09-24T12:02Z
  - log: 2026-09-24T14:21:03Z @kj amended text "after a page reload a background fish tab, once shown, has dozens of stacked right-prompt rows; cause: JupyterLab `Terminal._onMessage` writes the replay into an xterm not yet opened or fitted, at 80x24; owner JupyterLab; fix: hold stdout until the xterm is fitted; `src/index.ts`" -> "after a page reload a background fish tab, once shown, has dozens of stacked right-prompt rows; cause: JupyterLab `Terminal._onMessage` writes the replay into an xterm not yet opened or fitted, at 80x24; owner JupyterLab; fix: on first open after stdout, reset the xterm and reconnect; `src/index.ts`"
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix here: JupyterLab @jupyterlab/terminal widget writes before open; a patch needs private members (_termOpened) that break silently on upgrade; report upstream
- [-] `DEF-WIDTH-4` **Unfitted widget resizes the PTY to 24x80** - MEDIUM; a hidden tab restored by a reload shrinks its PTY to 24x80 until shown, and every reload flips a visible tab's PTY to 80 columns and back; cause: `_initialConnection` sends `set_size` with the unopened xterm's 24x80; owner JupyterLab; fix: no `set_size` before fit; `src/index.ts`
  - related: ACC-WIDTH-50 - the fix criterion
  - repro: reload the page with a fish tab in the background; the server receives `set_size` [24, 80] for it and resizes its PTY to 24x80
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj `_setSessionSize` sends `_term.rows` and `_term.cols`, which stay 24x80 until the xterm is opened and fitted; terminado `resize_to_smallest` applies them to the PTY for every client; proven in E2 T5 (24x80 from +8.14 s to +11.47 s) and E1 S3
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj found by `research-fish-width.spec.ts` T5 and the `research-replay-queries.spec.ts` reload test
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix here: JupyterLab @jupyterlab/terminal widget sends set_size before fit; patch needs private members (_setSessionSize); report upstream
- [-] `DEF-WIDTH-5` **Reconnected socket sends no set_size** - MEDIUM; after a socket drop or a lab restart the PTY keeps another client's width or the 24x80 spawn size, and fish stacks right-prompt rows on each keystroke; cause: `_initialConnection` disconnects itself after the first connect; owner JupyterLab; fix: send `set_size` on every connect; `src/index.ts`
  - related: ACC-WIDTH-52 - the fix criterion
  - repro: wide and narrow page on one terminal; drop the narrow socket with code 4000; type in the narrow page: new stacked rows
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj a socket that never sends `set_size` keeps size (None, None), which terminado `resize_to_smallest` skips; proven in E2 T3 (27 keystrokes add 38 stacked rows at 77 columns on a 177-column PTY) and T2 (new shell stays 24x80 in a 177x63 xterm)
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj found by `research-fish-width.spec.ts` T2 and T3
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix here: JupyterLab @jupyterlab/terminal _initialConnection sends set_size once; patch needs private members; report upstream
- [-] `DEF-WIDTH-6` **Replay rendered wider than the attaching xterm** - MEDIUM; a client narrower than the PTY width that history was rendered at shows stacked right-prompt rows even when fitted; cause: terminado replays raw output from every past PTY width; owner terminado; fix: decision pending, `suppress_buffer_replay` removes it together with the scrollback; `__init__.py`
  - repro: a 177-column page runs 2 commands; a 77-column page attaches to the same terminal: stacked right-prompt rows
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj fish places the right prompt with CR plus `CSI <W-1-len> C` for PTY width W; a narrower xterm wraps it and each redraw adds a row; proven in E2 T3 (31 rows at 77 columns from 177-column history) and T4 (`replay_4` at 163 columns: 12 rows, clean only at 245)
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj any `fish_right_prompt` stacks, the system prompt script is not the cause (E2 ablation with a `[R]` right prompt)
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix: replayed output is cursor-positioned for past widths and cannot be re-laid out; DEFAULTS['suppress_buffer_replay'] already exists for users who prefer no history
- [-] `DEF-WIDTH-7` **Reconnect appends a second copy of history** - MINOR; after a socket drop the xterm shows its history twice, and after a lab restart the new shell's banner starts at the dead shell's cursor; cause: the widget keeps its xterm on reconnect and terminado replays again; owner JupyterLab; fix: reset the xterm before a reconnect's replay; `src/index.ts`
  - related: ACC-WIDTH-54 - the fix criterion
  - repro: drop a fish terminal's socket with code 4000 and let it reconnect; scroll back: history repeated
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj `Terminal` is not reset when its session reconnects, so the replay is appended to the kept buffer; proven in E2 T3 (247 to 494 lines, 8 to 16 prompt rows) and T2 (banner written at row 5 column 71 of the old screen)
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj the duplication was first addressed by `suppress_buffer_replay` (journal entry 13), off by default since v1.0.8
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix here: JupyterLab @jupyterlab/terminal does not reset the xterm on reconnect; report upstream

## Output filter `FILTER`

Wrong deletions or misses of the `FILTER_PATTERNS` output filter in `handlers.py`

- [x] `DEF-FILTER-8` **Live OSC 4 palette query deleted** - MEDIUM; a program that sends `ESC]4;1;?` gets no answer and waits for its timeout; cause: the `(?!\?)` check in `ESC_OSC` looks at the palette index after `4;`, so the query matches as a response; fix: check for `?` after the index; `handlers.py`
  - evidence: ESC_OSC lookahead moved after the palette index; OSC 4 query tests green, red when reverted; 101 pytest green
  - blocked-by: DEF-REPLY-1 - the OSC 4 fix lets OSC 4 queries into the replay
  - related: ACC-GUARD-49 - the fix criterion
  - repro: `filter_terminal_responses('\x1b]4;1;?\x07')` returns empty text
  - test-tags: UNIT
  - root-cause: 2026-09-24T14:18:35Z @kj `ESC_OSC` is `\x1b\](?:4|10|11|12);(?!\?)...`; for OSC 4 the byte after `4;` is the index, so `ESC]4;1;?BEL` passes the check and is deleted; proven in E1 S7 (probe got 0 replies) and by a direct call on 2026-09-24
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj found by the `research-replay-queries.spec.ts` inventory; this deletion is also why OSC 4 never leaked on re-attach, so the fix lands with or after the replay strip
  - log: 2026-09-24T16:03:32Z @kj closed
- [-] `DEF-FILTER-9` **Output filter leaves the reply in fish** - MEDIUM; with the filter on, re-attach still leaves `]11;rgb:..\` and `[?1;2c` in fish's command line and on screen, and `bare_osc` deletes the copies from fish's `Unknown command` lines; cause: the filter sees only output and fish echoes the insert in pieces; fix: decision pending after the replay strip; `handlers.py`
  - repro: run `research-replay-queries.spec.ts` with `filter_osc_color_responses` true and false: same stdin replies and command lines
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj fish 3.7 echoes inserted text split at `;` and by colour codes (`ESC[91m]11ESC[32m;ESC[91mrgb:..`), which no contiguous pattern matches, and the text fish holds is input the filter never sees; proven in E1 S8 (filter on and off identical)
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj found by `research-replay-queries.spec.ts` in the filter-on and filter-off runs
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix: DEF-REPLY-1 fix removes the replies at their source; changing the bare_* patterns would reopen ACC-FILTER-6..14 for no remaining gain
- [-] `DEF-FILTER-11` **Colour set commands deleted** - MINOR; a program that sets a colour, e.g. `ESC]11;#282828 BEL` or `ESC]4;1;rgb:ff/00/00 ST` (pywal, base16-shell), sees no effect in a lab terminal; cause: `ESC_OSC` removes every OSC 4/10/11/12 payload not starting with `?`, since v1.0.10
  - repro: in a lab terminal run printf "\e]11;#282828\a"; the background does not change
  - test-tags: UNIT
  - root-cause: 2026-09-24T16:36:29Z @kj a colour set in the xterm.js reply form `ESC]11;rgb:xxxx/xxxx/xxxx ST` is byte-identical to a response, so no pattern on output separates the two; found by the 2026-09-24 adversarial review, round 1
  - log: 2026-09-24T16:36:29Z @kj added
  - log: 2026-09-24T16:36:30Z @kj rejected: won't fix: pre-existing since v1.0.10 and not reported; a pattern can only separate some set forms from responses, and changing the always-on filter would change v1.0.14 behaviour

## Keyboard input `KEYS`

Keys xterm.js sends to the shell that the user meant for the browser

- [-] `DEF-KEYS-10` **F11 inserts [23~ into the shell** - MINOR; `[23~` appears at the fish prompt and `^[[23~` during a running script; cause: xterm.js sends F11 as `ESC[23~`, the tty echoes it and fish inserts it without the ESC; owner xterm.js key mapping and the user's keystroke; fix: decision pending, a frontend key handler; `src/index.ts`
  - attachment: ../paste-20260924-140505.png sha256:5bc136c85ddf8f41 edited:2026-09-24T12:05:06Z
  - repro: focus a fish terminal, press F11
  - test-tags: FUNCTIONAL
  - root-cause: 2026-09-24T14:18:35Z @kj mechanism proven headless in E1 S9 (one `stdin` frame `ESC[23~`, command line `[23~`, `^[[23~` echoed during `sleep 3`); likely cause for the screenshot: F11 pressed for browser fullscreen and also passed to the page, not confirmed on the user's browser
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj reported: `^[[23~` after `Done` and 2 `[23~` rows in screenshot `paste-20260924-140505.png`; none of 22 tested queries produces `ESC[23~`
  - log: 2026-09-24T14:18:43Z @kj attached ../paste-20260924-140505.png sha256:5bc136c85ddf8f41
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix: a real F11 key press sent as designed by xterm.js; blocking it needs a frontend release and takes F11 from terminal apps

