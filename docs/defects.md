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

- [x] `DEF-WIDTH-3` **Background tab parses its replay at 80x24** - MEDIUM; after a page reload a background tab, once shown, has history laid out for 80 columns: stacked prompt rows in fish, stacked frames in Codex; cause: JupyterLab writes the replay into an unfitted 80x24 xterm; fix: plugin calls public `refresh()` once at first open; `src/unopenedTerminal.ts`
  - evidence: `holdUntilOpened` calls `refresh()` once at first open; Galata `background-terminal.spec.ts` test a failed on 1.0.15 (markers [2, 2, 1, 1], 1 open) and passes on 1.0.16 in fish and bash; E3 on the build: 0 duplicates in both shells; adversarial review SHIP in round 3
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
  - log: 2026-10-12T04:17:39Z @kj reported again 2026-10-12: Codex 0.162.1 tab, scrollback holds stacked overlapping frames; 3 pasted rows are exactly 80 chars while PTY is 55x165; server log shows 5-terminal attach bursts at 05:12:59 and 05:30:11
  - log: 2026-10-12T04:43:51Z @kj fix hypothesis 2026-10-12, untested: call public `ITerminal.refresh()` once after the widget's first fit, detected by a Lumino message hook on `update-request`; needs no private member, so the rejection reason may not hold
  - log: 2026-10-12T05:32:28Z @kj reopened: reopened: user asked for the fix on 2026-10-12; public `ITerminal.refresh()` needs no private member
  - log: 2026-10-12T06:27:30Z @kj amended text "after a page reload a background fish tab, once shown, has dozens of stacked right-prompt rows; cause: JupyterLab `Terminal._onMessage` writes the replay into an xterm not yet opened or fitted, at 80x24; owner JupyterLab; fix: on first open after stdout, reset the xterm and reconnect; `src/index.ts`" -> "MEDIUM; after a page reload a background tab, once shown, has history laid out for 80 columns: stacked prompt rows in fish, stacked frames in Codex; cause: JupyterLab writes the replay into an unfitted 80x24 xterm; fix: plugin calls public `refresh()` once at first open; `src/unopenedTerminal.ts`"
  - log: 2026-10-12T08:21:36Z @kj closed
- [x] `DEF-WIDTH-4` **Unfitted widget resizes the PTY to 24x80** - MEDIUM; a hidden tab restored by a reload shrinks its PTY to 24x80 until shown, so programs in it draw for 80x24; cause: `_initialConnection` sends `set_size` with the unopened xterm's 24x80; owner JupyterLab; fix: the frontend plugin holds `set_size` back until the xterm is opened; `src/unopenedTerminal.ts`
  - evidence: a `set_size` sent before the xterm is opened is held back; Galata test a: no [24, 80] frame after the reload (1.0.15 sent [[24, 80], [59, 254]]); E3 on build 1.0.16: PTY 59x177 while hidden, never 80 columns, in 10 of 10 hidden runs
  - related: ACC-WIDTH-50 - the fix criterion
  - repro: reload the page with a fish tab in the background; the server receives `set_size` [24, 80] for it and resizes its PTY to 24x80
  - test-tags: FUNCTIONAL
  - root-cause: 2026-10-12T06:27:03Z @kj E3: a hidden restored tab sends `set_size` [24, 80, 903, 1522] 28 to 122 ms after the widget is created, in 30 of 30 runs; the pixel offsets are real, so the server cannot tell it from a fitted size; the PTY is 80x24 from 1.90 to 2.57 s after the reload until the tab is shown
  - root-cause: 2026-09-24T14:18:35Z @kj `_setSessionSize` sends `_term.rows` and `_term.cols`, which stay 24x80 until the xterm is opened and fitted; terminado `resize_to_smallest` applies them to the PTY for every client; proven in E2 T5 (24x80 from +8.14 s to +11.47 s) and E1 S3
  - log: 2026-09-24T14:18:35Z @kj added
  - log: 2026-09-24T14:18:43Z @kj found by `research-fish-width.spec.ts` T5 and the `research-replay-queries.spec.ts` reload test
  - log: 2026-09-24T14:24:52Z @kj rejected: won't fix here: JupyterLab @jupyterlab/terminal widget sends set_size before fit; patch needs private members (_setSessionSize); report upstream
  - log: 2026-10-12T06:27:03Z @kj reopened: reopened: experiment E3 on 2026-10-12 showed that redraw alone leaves lost and stale lines for a program that addresses rows absolutely, because the PTY was 24x80 while the tab was hidden
  - log: 2026-10-12T06:27:03Z @kj root-cause overridden; reason: measured payload replaces the source-reading guess of -1 offsets
  - log: 2026-10-12T06:27:03Z @kj amended text "a hidden tab restored by a reload shrinks its PTY to 24x80 until shown, and every reload flips a visible tab's PTY to 80 columns and back; cause: `_initialConnection` sends `set_size` with the unopened xterm's 24x80; owner JupyterLab; fix: no `set_size` before fit; `src/index.ts`" -> "MEDIUM; a hidden tab restored by a reload shrinks its PTY to 24x80 until shown, so programs in it draw for 80x24; cause: `_initialConnection` sends `set_size` with the unopened xterm's 24x80; owner JupyterLab; fix: the frontend plugin holds `set_size` back until the xterm is opened; `src/unopenedTerminal.ts`"
  - log: 2026-10-12T08:21:36Z @kj closed
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
- [-] `DEF-WIDTH-12` **Redraw keeps the old cursor row** - MINOR; after the background-tab redraw the first buffer row holds the old cursor row followed by the first replayed line; seen in 2 of 2 S1 runs on build 1.0.16; owner JupyterLab
  - related: DEF-WIDTH-3 - the redraw that leaves this row
  - repro: E3 spec, scenario S1: compare buffer row 0 after the tab is shown with row 0 before the reload
  - test-tags: FUNCTIONAL
  - root-cause: 2026-10-12T07:15:49Z @kj JupyterLab `refresh()` calls xterm `clear()`, which keeps the cursor row and column, so the replay continues on that row
  - log: 2026-10-12T07:15:49Z @kj added
  - log: 2026-10-12T07:16:24Z @kj rejected: won't fix: one row at the top of the redrawn history; a cure needs a line-erase prefix on every server replay or the private xterm `reset()`; stated as a limit in the README
- [-] `DEF-WIDTH-13` **History before an alternate screen keeps 80x24** - MINOR; in a background tab whose program entered the alternate screen within the replayed history, the lines printed before that program keep the 80x24 layout after the redraw; visible once the program exits; 4 changed rows with and without the fix; owner JupyterLab
  - related: DEF-WIDTH-3 - the redraw does not reach these rows
  - repro: E3 spec, scenario S3: compare the normal buffer after the program left the alternate screen with the buffer before the reload
  - test-tags: FUNCTIONAL
  - root-cause: 2026-10-12T07:15:49Z @kj `refresh()` clears the active buffer only, and the second replay starts while the alternate buffer is active, so the normal buffer keeps the first parse
  - log: 2026-10-12T07:15:49Z @kj added
  - log: 2026-10-12T07:16:24Z @kj rejected: won't fix: same rows as before the fix; a cure needs the private xterm `reset()`; stated as a limit in the README
- [-] `DEF-WIDTH-15` **Redraw drops output older than the replay** - MEDIUM; at first show the redraw replaces the terminal's buffer with the server's replay, the last 1000 output chunks; older output received while the tab was hidden is dropped, build 1.0.15 kept it; 1602 chunks while hidden: 2 early marker lines gone, 1612 dots become 1006; setting off keeps it
  - related: DEF-WIDTH-3 - the redraw that replaces the buffer
  - repro: print a marker, put another tab in front, reload, print 1600 chunks, show the tab; spec `horizon.spec.ts` is kept in `tmp/research/fix2/horizon/`, and its two imports resolve only from `ui-tests/tests/`
  - test-tags: FUNCTIONAL
  - root-cause: 2026-10-12T08:00:29Z @kj JupyterLab `refresh()` is `session.reconnect()` then xterm `clear()`; terminado keeps `read_buffer = deque([], maxlen=1000)` with one entry per PTY read
  - log: 2026-10-12T08:00:29Z @kj added
  - log: 2026-10-12T08:00:35Z @kj found by adversarial review round 1 (bug-hunter); evidence `tmp/research/fix2/horizon/horizon-8905.log` RESULT lines 204 and 247; code cure deferred: it needs a private member or a server change; whether the default stays on is the owner's decision
  - log: 2026-10-12T08:12:11Z @kj edited repro "run `tmp/research/fix2/horizon/horizon.spec.ts` on the test server: print a marker, put another tab in front, reload, print 1600 chunks, show the tab" -> "print a marker, put another tab in front, reload, print 1600 chunks, show the tab; spec `horizon.spec.ts` is kept in `tmp/research/fix2/horizon/`, and its two imports resolve only from `ui-tests/tests/`"
  - log: 2026-10-12T10:29:20Z @kj rejected: won't fix: owner's decision on 2026-10-12 - the default stays on and the README states the limit; the setting "Redraw background terminals when first shown" off keeps the output
- [x] `DEF-WIDTH-16` **New terminal reconnects at creation** - MINOR; a terminal created on a fresh page reconnects once at creation when its shell prints before the xterm module has loaded: bare bash, 2 websocket opens in 3 of 4 runs on build 1.0.16; fish 0 of 8; no visible change; fix: count only stdout received while hidden
  - evidence: `holdUntilOpened` counts stdout only while `terminal.isVisible` is false; Galata `a terminal the user creates is not reconnected` with bare bash: 4 of 4 failed on 1.0.16 (2 opens), 4 of 4 pass on 1.0.17; jest 11 of 11, mutation without the condition fails 1 case
  - repro: `TEST_TERMINAL_SHELL='/bin/bash --norc --noprofile'`, fresh page, `terminal:create-new`, count websocket opens of the new terminal
  - test-tags: UNIT, FUNCTIONAL
  - root-cause: 2026-10-12T10:35:56Z @kj the redraw was triggered by any stdout before the xterm open; for a visible new terminal that is the wait for the xterm module, not a hidden tab
  - log: 2026-10-12T10:35:56Z @kj added
  - log: 2026-10-12T10:43:55Z @kj closed

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

## Repaint on attach `BOUNCE`

Side effects of the PTY size bounce that makes programs repaint after a client attaches

- [-] `DEF-BOUNCE-14` **Bounce interval costs one line** - MINOR; a program that addresses rows absolutely and commits a line while the PTY is one row taller (for 0.12 s, starting 0.4 s after a websocket open) loses that line or leaves one stale row; stand-in: 1 of 3 runs with `repaint_on_attach` on, 0 of 3 with it off; the background-tab redraw adds one such interval at first show
  - repro: E3 spec, scenario S2a on build 1.0.16, repeated; compare `side.jsonl` commit times with `setwinsize` events in `server.jsonl`
  - test-tags: FUNCTIONAL
  - root-cause: 2026-10-12T07:15:49Z @kj `_make_winsize_bounce` sets rows + 1 for `_BOUNCE_STEP`; a frame drawn for the taller size lands one row off in the xterm
  - log: 2026-10-12T07:15:49Z @kj added; reason: the text carries the measured rates of both arms and the link to the redraw
  - log: 2026-10-12T07:16:25Z @kj rejected: won't fix: any PTY size change has this interval, and the size must change because Node programs ignore a SIGWINCH without one; `DEFAULTS['repaint_on_attach']` off removes it
  - log: 2026-10-12T08:00:35Z @kj amended text "a program that addresses rows absolutely and commits a line while the PTY is one row taller (0.12 s after a websocket open) loses that line or leaves one stale row; stand-in: 1 of 4 runs with `repaint_on_attach` on, 0 of 3 with it off; the background-tab redraw adds one such interval at first show" -> "MINOR; a program that addresses rows absolutely and commits a line while the PTY is one row taller (for 0.12 s, starting 0.4 s after a websocket open) loses that line or leaves one stale row; stand-in: 1 of 3 runs with `repaint_on_attach` on, 0 of 3 with it off; the background-tab redraw adds one such interval at first show"; reason: the text carries the measured rates of both arms and the link to the redraw

