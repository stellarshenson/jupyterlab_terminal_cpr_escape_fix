# Acceptance Criteria and Tests

This document defines what the terminal filter must do, what it must never do, and
maps each criterion to the test that enforces it. It exists so a future change to
the regex set can be judged against intent, not guesswork - every "filter this"
rule is paired with a "but protect that" rule.

## Overview

The extension patches `TermSocket.on_pty_read` server-side and runs every chunk of
PTY output through `filter_terminal_responses()` in `handlers.py`. The function
strips terminal query _responses_ that leak as literal text when reconnecting to an
idle terminal, while leaving genuine terminal output untouched. Tests live in
`jupyterlab_terminal_cpr_escape_fix/tests/test_handlers.py` (67 tests).

## What must be filtered

These are terminal-to-shell _responses_. Fish (and similar shells) echo them as
literal text on reconnect, sometimes with the ESC byte stripped from the introducer
and the ST terminator, so each type is filtered in both ESC-prefixed and bare form.

- CPR cursor position report - `ESC[row;colR` and bare `[row;colR`
- DA device attributes - `ESC[?p1;p2c` and bare `[?p1;p2c`
- DA2 secondary attributes - `ESC[>p1;p2;p3c` and bare `[>p1;p2;p3c`
- DECRPM mode report - `ESC[?mode;value$y` and bare `[?mode;value$y`
- OSC color response - `ESC]N;rgb:..ST` for N in 4/10/11/12, and bare `]N;rgb:..\`

The bare OSC color response is the case that motivated this revision. Fish strips
ESC from both the `]` introducer and the ST terminator, so `ESC]11;rgb:..ST` arrives
as `]11;rgb:..\` and slipped past every earlier pattern. The `rgb:`-anchored regex
catches it while keeping the false-positive surface near zero.

| Criterion                   | Sequence              | Test                                       |
| --------------------------- | --------------------- | ------------------------------------------ |
| CPR filtered                | `ESC[52;1R`           | `test_filters_cpr`                         |
| DA filtered                 | `ESC[?1;2c`           | `test_filters_da`                          |
| DA2 filtered                | `ESC[>0;276;0c`       | `test_filters_da2`                         |
| DECRPM filtered             | `ESC[?12;2$y`         | `test_filters_decrpm`                      |
| OSC 10/11 filtered          | `ESC]10;rgb:..ST`     | `test_filters_osc10`, `test_filters_osc11` |
| Bare CPR filtered           | `[2;1R`               | `test_filters_bare_cpr`                    |
| Bare DA filtered            | `[?1;2c`              | `test_filters_bare_da`                     |
| Bare DA2 filtered           | `[>0;276;0c`          | `test_filters_bare_da2`                    |
| Bare DECRPM filtered        | `[?12;2$y`            | `test_filters_bare_decrpm`                 |
| Bare OSC color filtered     | `]10;rgb:..\`         | `test_filters_bare_osc_color_response`     |
| Bare OSC multi filtered     | two `]N;rgb:..\`      | `test_filters_multiple_bare_osc`           |
| Bare OSC 4 palette filtered | `]4;1;rgb:..\`        | `test_filters_bare_osc4_palette`           |
| Full leaked prompt cleaned  | mixed leak -> `clear` | `test_bare_osc_full_leaked_prompt`         |
| Full fish response cleaned  | all types -> ``       | `test_fish_shell_full_response`            |

## What must be protected

These must pass through unchanged. They are either genuine terminal output, _queries_
(shell-to-terminal requests - stripping them breaks capability negotiation), or plain
text that resembles a sequence. This is the half that guards against over-filtering.

| Criterion                       | Sequence                                        | Test                                                                                                |
| ------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| SGR colors preserved            | `ESC[38;5;231m`, `ESC[38;2;..m`, `ESC[0m`       | `test_preserves_sgr_color_256`, `test_preserves_sgr_color_rgb`, `test_preserves_sgr_reset`          |
| Cursor movement preserved       | `ESC[5A/3B/71C/2D`                              | `test_preserves_cursor_up`/`_down`/`_forward`/`_back`                                               |
| Cursor position (CUP) preserved | `ESC[10;20H`                                    | `test_preserves_cursor_position`                                                                    |
| Erase / scroll preserved        | `ESC[K`, `ESC[2J`, `ESC[3S`                     | `test_preserves_erase_line`/`_display`/`_scroll_up`                                                 |
| DEC private modes preserved     | `ESC[?2004h`, `ESC[?1049h`, `ESC[?25h`          | `test_preserves_bracketed_paste_mode`, `_alternate_screen`, `_dec_private_mode_set`                 |
| OSC 0/7/8/133 preserved         | title, cwd, hyperlink, prompt mark              | `test_preserves_window_title_osc0`, `_osc7_cwd`, `_osc8_hyperlink`, `_osc133_prompt_mark`           |
| OSC color queries preserved     | `ESC]10;?`, `ESC]11;?`, `ESC]12;?`              | `test_preserves_osc10_query`/`_osc11_query`/`_osc12_query`                                          |
| DA / DA2 queries preserved      | `ESC[c`, `ESC[?c`, `ESC[>c`, `ESC[>0c`          | `test_preserves_da_query`, `test_preserves_da2_query`                                               |
| OSC 52 clipboard preserved      | BEL, ST, empty, primary, large payload          | `test_preserves_osc52_*` (5 tests)                                                                  |
| Plain bracket text preserved    | `array[0]`, `matrix[3][5]`, markdown, git, JSON | `test_preserves_array_index`, `_matrix_notation`, `_markdown_link`, `_git_output`, `_json_brackets` |
| Bare OSC needs rgb: payload     | `note]10; and continue`                         | `test_bare_osc_preserves_plain_text_close_bracket`                                                  |
| Bare OSC query preserved        | `]11;?\`                                        | `test_bare_osc_preserves_bare_osc_query`                                                            |
| Bare OSC no double-count        | `ESC]10;rgb:..ST` counted once as `osc`         | `test_bare_osc_does_not_double_count_esc_prefixed`                                                  |

## Toggle behaviour

The bare OSC color filter is the newest and broadest pattern, so it is gated by a
default toggle in case it misbehaves in an unforeseen environment. `DEFAULTS` in
`__init__.py` holds `filter_osc_color_responses` (default `True`). When `False`,
`_load_jupyter_server_extension` removes the `bare_osc` entry from `FILTER_PATTERNS`
before patching, so the bare OSC color response is left untouched while every other
filter stays active. The toggle is internal - not exposed as a user setting.

- `filter_osc_color_responses: True` - bare OSC color responses filtered (default)
- `filter_osc_color_responses: False` - bare OSC color responses pass through
- `suppress_buffer_replay: False` - terminado buffer replay suppression (default off)

## Regression protection

Any new pattern added to `FILTER_PATTERNS` must add both a "filter this" test and at
least one "protect that" test proving it does not strip the nearest legitimate
look-alike. The bare OSC addition follows this: it filters `]N;rgb:..\` but is proven
to leave plain `]10;` text and `]N;?` queries intact. Run the full suite with
`make test` (or `python -m pytest jupyterlab_terminal_cpr_escape_fix/tests/`) - all
67 tests must pass before release.

## Observed effects

Running log of effects seen in real use - desired effects and side effects alike.
Each entry is keyed by the commit id and date/time of the state that produced the
observation, so any effect can be back-checked against the exact code that caused it.
Record both what was fixed and any new behaviour or regression, even if benign.

Format: `commit` (short id) - `date/time` - `effect` (desired / side effect) -
description, with the deciding evidence and the test that now covers it (if any).

| Commit    | Date/time        | Effect                              | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------- | ---------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `4c411ea` | 2026-05-31 13:55 | desired                             | Bare OSC color responses (`]10;rgb:..\`, `]11;rgb:..\`) no longer leak as literal text on reconnect to an idle fish terminal. Diagnosed by feeding the exact leaked bytes through `filter_terminal_responses()`; covered by `test_filters_bare_osc_color_response` and `test_bare_osc_full_leaked_prompt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `4c411ea` | 2026-05-31 13:55 | side effect (guarded)               | New `bare_osc` pattern could over-strip plain text shaped like `]10;..\`; constrained to an `rgb:`-anchored payload. Plain `]10;` text and `]N;?` queries verified intact by `test_bare_osc_preserves_plain_text_close_bracket` and `test_bare_osc_preserves_bare_osc_query`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `5cc6a11` | 2026-06-09 13:47 | not a code defect (runtime / scope) | `home` (`~`) terminal showed `du -h -s .git` fragmenting across repeated prompt repaints during `sync_home_prune.sh`. Investigated via Playwright + server log. The shipped filter is correct: feeding a representative leak through the on-disk `filter_terminal_responses()` returns clean `du -h -s .git` (`cpr:2, bare_osc:2`). This container's server (`19c12ea09253`, PID 101) runs v1.0.11 with the on-disk build byte-identical to `4c411ea` and logs `Patched TermSocket — CPR filter` at startup, yet shows zero `FILTERED` flushes across 6 days of `/var/log/jupyterlab.log` - so the artifact-producing terminal is most likely on the second server container (`2799ce9a80ac`, also root `/home/lab/workspace`) which cannot be version-checked from here. Two distinct artifact classes: (1) literal CPR/OSC escape leakage - what the filter targets, now absent from the new paste; (2) prompt-repaint fragmentation after a heavy `\r` progress flood - cosmetic cursor-repaint desync the response filter does not address. Action: verify/`make install` v1.0.11 on container `2799ce9a80ac` and restart its server. No test change |
| `5cc6a11` | 2026-06-09 14:20 | root cause found + fixed (external) | Prompt-repaint fragmentation (class 2 above) root-caused to the fish right prompt, not this extension. `/home/lab` is a 2.7 GB git repo and `__stellars_git_info` in `/etc/fish/functions/fish_prompt.fish` ran `git diff --numstat` on every render to count modified files - 1.66 s of the 1.70 s total render in `~`. Slow async right prompt arrived out of step with the redraw, smearing ` main 7s` and the next command across half-drawn frames. Patched line 321 `git diff --numstat` -> `git diff --name-only` (identical 17-file count, full per-file line diff avoided); total prompt render dropped 1.70 s -> 0.136 s (12.5x). Verified via `fish -n` syntax check and live `fish_right_prompt` render (`main !4`). Backup at `/etc/fish/functions/fish_prompt.fish.bak-20260609-142057`. Not a code change to this extension; confirms the artifact was prompt latency, not escape leakage                                                                                                                                                                                                                                                 |
