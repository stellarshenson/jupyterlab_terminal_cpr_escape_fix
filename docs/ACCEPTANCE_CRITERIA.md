# Acceptance Criteria - Terminal Response Filter and Reconnect Recovery

Server-side patch of `TermSocket` in jupyter_server_terminals: filters terminal
query responses out of PTY output before they reach the browser, and after a
client attach forces a full app repaint via a PTY winsize bounce. One
consolidated doc for the plugin; tests live in
`jupyterlab_terminal_cpr_escape_fix/tests/test_handlers.py` (71 tests).

## Contents

- [Filter criteria](#filter-criteria)
- [Protection criteria](#protection-criteria)
- [Toggle behaviour](#toggle-behaviour)
- [Repaint on attach](#repaint-on-attach)
- [Regression protection](#regression-protection)
- [Observed effects](#observed-effects)

## Filter criteria

Terminal-to-shell responses that fish echoes as literal text on reconnect, each
filtered in both ESC-prefixed and bare form (fish strips ESC from the
introducer and the ST terminator).

- [x] **CPR filtered** - `ESC[52;1R` stripped (`test_filters_cpr`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **DA filtered** - `ESC[?1;2c` stripped (`test_filters_da`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **DA2 filtered** - `ESC[>0;276;0c` stripped (`test_filters_da2`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **DECRPM filtered** - `ESC[?12;2$y` stripped (`test_filters_decrpm`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **OSC 10/11 filtered** - `ESC]10;rgb:..ST` and `ESC]11;rgb:..ST` stripped (`test_filters_osc10`, `test_filters_osc11`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Bare CPR filtered** - `[2;1R` stripped (`test_filters_bare_cpr`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Bare DA filtered** - `[?1;2c` stripped (`test_filters_bare_da`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Bare DA2 filtered** - `[>0;276;0c` stripped (`test_filters_bare_da2`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Bare DECRPM filtered** - `[?12;2$y` stripped (`test_filters_bare_decrpm`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Bare OSC color filtered** - `]10;rgb:..\` stripped (`test_filters_bare_osc_color_response`)
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Bare OSC multi filtered** - two `]N;rgb:..\` in one chunk both stripped (`test_filters_multiple_bare_osc`)
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Bare OSC 4 palette filtered** - `]4;1;rgb:..\` with palette index stripped (`test_filters_bare_osc4_palette`)
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Full leaked prompt cleaned** - the exact leaked byte mix reduces to `clear` (`test_bare_osc_full_leaked_prompt`)
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Full fish response cleaned** - all response types in one chunk fully stripped (`test_fish_shell_full_response`)
  - log: 2026-05-31 documented (v1.0.10)

## Protection criteria

Genuine terminal output, shell-to-terminal queries, and plain text that
resembles a sequence must pass through unchanged - the half that guards against
over-filtering.

- [x] **SGR colors preserved** - `ESC[38;5;231m`, `ESC[38;2;..m`, `ESC[0m` untouched (`test_preserves_sgr_color_256`, `test_preserves_sgr_color_rgb`, `test_preserves_sgr_reset`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Cursor movement preserved** - `ESC[5A/3B/71C/2D` untouched (4 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Cursor position preserved** - `ESC[10;20H` untouched (`test_preserves_cursor_position`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Erase and scroll preserved** - `ESC[K`, `ESC[2J`, `ESC[3S` untouched (3 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **DEC private modes preserved** - `ESC[?2004h`, `ESC[?1049h`, `ESC[?25h` untouched (3 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **OSC 0/7/8/133 preserved** - title, cwd, hyperlink, prompt mark untouched (4 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **OSC color queries preserved** - `ESC]10;?`, `ESC]11;?`, `ESC]12;?` untouched (3 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **DA and DA2 queries preserved** - `ESC[c`, `ESC[?c`, `ESC[>c`, `ESC[>0c` untouched (`test_preserves_da_query`, `test_preserves_da2_query`)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **OSC 52 clipboard preserved** - BEL, ST, empty, primary, large payload variants untouched (5 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Plain bracket text preserved** - `array[0]`, matrix, markdown link, git output, JSON brackets untouched (5 tests)
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Bare OSC needs rgb: payload** - `note]10; and continue` untouched (`test_bare_osc_preserves_plain_text_close_bracket`)
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Bare OSC query preserved** - `]11;?\` untouched (`test_bare_osc_preserves_bare_osc_query`)
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Bare OSC no double-count** - `ESC]10;rgb:..ST` counted once as `osc`, not again as `bare_osc` (`test_bare_osc_does_not_double_count_esc_prefixed`)
  - log: 2026-05-31 implemented (v1.0.10)

## Toggle behaviour

Toggles live in `DEFAULTS` in `__init__.py` and are internal, not user settings.

- [x] **Toggle: filter_osc_color_responses** - True filters bare OSC color responses (default), False drops the `bare_osc` pattern before patching
  - log: 2026-05-31 implemented (v1.0.10)
- [x] **Toggle: suppress_buffer_replay** - False leaves the terminado replay intact (default), True silences `on_pty_read` during `open()`
  - log: 2026-05-31 documented (v1.0.10)
- [x] **Toggle: repaint_on_attach** - True bounces PTY winsize after attach (default), False leaves reconnect behaviour untouched
  - log: 2026-08-13 implemented (v1.0.12)

## Repaint on attach

The replay window holds only incremental diff frames, so a fresh client (window
refresh) never receives static regions - the Claude Code status line and input
box vanish and the live stream never repaints them (verified 2026-08-13, see
Observed effects). After the replay drains, `_make_winsize_bounce` nudges the
PTY one row taller and back; each size change makes the kernel deliver SIGWINCH
and the foreground app repaints its full screen.

- [x] **Bounce grows then restores** - PTY set one row taller, original size restored one step later (`test_bounce_grows_then_restores`)
  - log: 2026-08-13 implemented (v1.0.12)
- [x] **Settle delay** - bounce fires 0.4 s after attach so client geometry is final
  - log: 2026-08-13 implemented (v1.0.12)
- [x] **Debounce** - at most one bounce per 5 s per terminal, so reconnect storms do not flicker-loop (`test_debounce_and_prune`)
  - log: 2026-08-13 implemented (v1.0.12); test pin added after review
- [x] **Prune inert debounce entries** - entries aged past the debounce window are deleted in place on the next scheduled bounce, so `_last_bounce` stays bounded (`test_debounce_and_prune`)
  - log: 2026-08-13 implemented (v1.0.12)
- [x] **Guarded restore** - restore write skipped when the size changed mid-bounce, a racing real client resize is never clobbered (`test_bounce_restore_guarded_against_racing_resize`)
  - log: 2026-08-13 implemented (v1.0.12)
- [x] **Edge: no winsize support** - terminal that cannot report its size is left untouched (`test_bounce_noop_when_getwinsize_fails`)
  - log: 2026-08-13 implemented (v1.0.12)
- [x] **Edge: grow write fails** - failed grow schedules no restore (`test_bounce_noop_when_setwinsize_fails`)
  - log: 2026-08-13 implemented (v1.0.12)
- [ ] **Live verification** - with the patch active, a window refresh leaves the Claude Code status line intact (requires `make install` and a server restart to load the patch; the installed copy predates the feature)
  - log: 2026-08-13 criterion added, pending make install + server restart

## Regression protection

Any new pattern added to `FILTER_PATTERNS` must add both a "filter this" test
and at least one "protect that" test proving it does not strip the nearest
legitimate look-alike. The bare OSC addition follows this: it filters
`]N;rgb:..\` but is proven to leave plain `]10;` text and `]N;?` queries
intact. Run the full suite with `make test` (or
`python -m pytest jupyterlab_terminal_cpr_escape_fix/tests/`) - all 71 tests
must pass before release.

## Observed effects

Running log of effects seen in real use - desired effects and side effects alike.
Each entry is keyed by the commit id and date/time of the state that produced the
observation, so any effect can be back-checked against the exact code that caused it.
Record both what was fixed and any new behaviour or regression, even if benign.

Format: `commit` (short id) - `date/time` - `effect` (desired / side effect) -
description, with the deciding evidence and the test that now covers it (if any).

| Commit    | Date/time              | Effect                                                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------- | ---------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `4c411ea` | 2026-05-31 13:55       | desired                                               | Bare OSC color responses (`]10;rgb:..\`, `]11;rgb:..\`) no longer leak as literal text on reconnect to an idle fish terminal. Diagnosed by feeding the exact leaked bytes through `filter_terminal_responses()`; covered by `test_filters_bare_osc_color_response` and `test_bare_osc_full_leaked_prompt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `4c411ea` | 2026-05-31 13:55       | side effect (guarded)                                 | New `bare_osc` pattern could over-strip plain text shaped like `]10;..\`; constrained to an `rgb:`-anchored payload. Plain `]10;` text and `]N;?` queries verified intact by `test_bare_osc_preserves_plain_text_close_bracket` and `test_bare_osc_preserves_bare_osc_query`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `5cc6a11` | 2026-06-09 13:47       | not a code defect (runtime / scope)                   | `home` (`~`) terminal showed `du -h -s .git` fragmenting across repeated prompt repaints during `sync_home_prune.sh`. Investigated via Playwright + server log. The shipped filter is correct: feeding a representative leak through the on-disk `filter_terminal_responses()` returns clean `du -h -s .git` (`cpr:2, bare_osc:2`). This container's server (`19c12ea09253`, PID 101) runs v1.0.11 with the on-disk build byte-identical to `4c411ea` and logs `Patched TermSocket - CPR filter` at startup, yet shows zero `FILTERED` flushes across 6 days of `/var/log/jupyterlab.log` - so the artifact-producing terminal is most likely on the second server container (`2799ce9a80ac`, also root `/home/lab/workspace`) which cannot be version-checked from here. Two distinct artifact classes: (1) literal CPR/OSC escape leakage - what the filter targets, now absent from the new paste; (2) prompt-repaint fragmentation after a heavy `\r` progress flood - cosmetic cursor-repaint desync the response filter does not address. Action: verify/`make install` v1.0.11 on container `2799ce9a80ac` and restart its server. No test change |
| `5cc6a11` | 2026-06-09 14:20       | root cause found + fixed (external)                   | Prompt-repaint fragmentation (class 2 above) root-caused to the fish right prompt, not this extension. `/home/lab` is a 2.7 GB git repo and `__stellars_git_info` in `/etc/fish/functions/fish_prompt.fish` ran `git diff --numstat` on every render to count modified files - 1.66 s of the 1.70 s total render in `~`. Slow async right prompt arrived out of step with the redraw, smearing ` main 7s` and the next command across half-drawn frames. Patched line 321 `git diff --numstat` -> `git diff --name-only` (identical 17-file count, full per-file line diff avoided); total prompt render dropped 1.70 s -> 0.136 s (12.5x). Verified via `fish -n` syntax check and live `fish_right_prompt` render (`main !4`). Backup at `/etc/fish/functions/fish_prompt.fish.bak-20260609-142057`. Not a code change to this extension; confirms the artifact was prompt latency, not escape leakage                                                                                                                                                                                                                                                 |
| `a4be605` | 2026-08-13 19:25-19:38 | side effect (external mechanism, not a filter defect) | Window refresh at 19:25:46.767 UTC (server log `TermSocket.open: 8` from 172.21.0.1) left the fresh client's Claude Code status line (`69% kimi-k3[1m] max main !2 base`) and input-box parts missing, unhealed for 12m19s. Byte-level capture via a detached Playwright recorder on terminal 8 (CDP WS frames + in-page WebSocket wrapper + screenshots): the terminado replay burst (144 chunks in 5 ms) holds only incremental diff frames - `kimi-k3`, `69%`, `main !` all absent - and the live stream sent zero status-line draws until the context percent changed at 19:38:05. Probe reload reproduced the torn screen (`shot-00197` vs `shot-00198`). Motivated `repaint_on_attach`; covered by `TestWinsizeBounce`                                                                                                                                                                                                                                                                                                                                                                                                                             |
