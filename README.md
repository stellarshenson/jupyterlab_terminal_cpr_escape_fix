# jupyterlab_terminal_cpr_escape_fix

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_terminal_cpr_escape_fix/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_terminal_cpr_escape_fix/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_terminal_cpr_escape_fix.svg)](https://www.npmjs.com/package/jupyterlab_terminal_cpr_escape_fix)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-terminal-cpr-escape-fix.svg)](https://pypi.org/project/jupyterlab-terminal-cpr-escape-fix/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-terminal-cpr-escape-fix)](https://pepy.tech/project/jupyterlab-terminal-cpr-escape-fix)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)

> [!TIP]
> This fix is part of the [stellars_jupyterlab_fixes](https://github.com/stellarshenson/stellars_jupyterlab_fixes) metapackage. Install all Stellars fixes at once: `pip install stellars_jupyterlab_fixes`

> [!WARNING]
> This extension provides a workaround for a known JupyterLab/terminado issue. It will be deprecated once JupyterLab addresses this problem in a GA release. Monitor the upstream issue tracker for official fixes.

Fix the JupyterLab terminado issue where returning to an idle terminal causes cursor position report (CPR) escape sequences to appear as literal text. This is particularly noticeable with fish shell, where sequences like `[2;2R[3;1R` or `[?1;2c[>0;276;0c` appear at the prompt after reconnecting.

## How it works

When a JupyterLab terminal sits idle, the shell (especially fish) periodically queries terminal capabilities. These queries accumulate in terminado's buffer. On reconnect, terminado replays that buffer, xterm.js answers the old queries again, and the shell inserts the answers as literal text.

This extension patches `TermSocket.on_pty_read()` server-side to filter terminal query responses before they reach the browser. It handles both ESC-prefixed sequences and bare remnants where fish shell has stripped the ESC byte.

**Filtered sequences** (terminal query responses):

- CPR - Cursor Position Report (`ESC[row;colR`)
- DA/DA2 - Device Attributes (`ESC[?...c`, `ESC[>...c`)
- DECRPM - DEC Report Mode (`ESC[?mode;value$y`)
- OSC 4/10/11/12 - Color query responses

**Preserved sequences** (functional terminal output):

- All SGR color codes, cursor movement, erase, scroll
- OSC 0 (window/tab title), OSC 7 (cwd), OSC 8 (hyperlinks)
- OSC 52 (clipboard - used by companion clipboard extension)
- OSC 133 (shell integration prompt marks)
- Bracketed paste mode, alternate screen, all DEC private modes

**Repaint on attach** (window refresh recovery):

- After a client attaches and the buffer replay drains, the PTY is set one column narrower for 0.12 s and back
- The kernel delivers SIGWINCH, so the foreground app (Claude Code, vim, htop) repaints its full screen
- Without it, a refreshed browser shows a torn screen: the replay holds only incremental diff frames, so static regions (status line, input box) are never delivered and never self-heal
- A column step, not a row step: a row step makes a program that addresses rows absolutely on the normal buffer write one row below the browser's last row and lose the line it commits during the step (measured across page reloads under stress: 0 of 10 damaged with the column step, 10 of 10 with the row step)
- One column narrower, not wider: a program that writes to the last column wraps its lines when the PTY is wider than the browser
- The clear before replay depends on it: with that clear, a plain reconnect erases the rows a full-screen program drew before the replay window, and only this repaint brings them back
- Limit: a real client resize to exactly one column less than the current width within the 0.12 s step is reverted, and the PTY is one column wider than that client until the next resize event
- No step while the foreground process group of the terminal is one shell alone, which the server treats as a shell at its prompt: the server reads the name of the group leader from `/proc/<os.tcgetpgrp(fd)>/comm` and its children from `/proc/<pid>/task/<pid>/children`, and makes no step when the name is `bash`, `sh`, `dash`, `zsh`, `fish`, `ksh`, `tcsh` or `csh` and no child is in the leader's process group; a shell at its prompt needs no repaint, because the replay restores its line; on a system without `/proc/<pid>/task/<pid>/children` the step always runs
- Why: a width step makes a line editor miscount the rows of a typed line that fills the width, so it erases the output line above the prompt; without the guard bash lost that line in 7 of 7 attaches with prompt plus typed text one or two terminal widths wide or one column less, with the guard in 0 of 7
- A shell with a child in its own process group is stepped: it runs a program without job control, and that program needs the repaint; a full-screen program started with `sh -c "<program>; true"` or with `bash <script>` kept its header and footer across a reconnect (1 before and 1 after in 3 of 3 for each)
- Limit: a line editor that is not one of these shells is still stepped; with a typed line one column less than the terminal width, `python3` 3.14.8 showed no change in 3 of 3 reconnects with its default REPL (pyrepl) and lost the output line above the prompt in 3 of 3 with `PYTHON_BASIC_REPL=1` (GNU readline); the same is expected, not measured, for a shell behind `ssh`, `sudo` or `docker exec`, where the local group leader is not a shell, and for a shell that keeps a child in its own process group while it is at its prompt (bash after `exec 3> >(cat >/dev/null)`)
- Limit: a full-screen program that is itself a shell script gets no step while the script waits in a shell builtin, because the group leader then has a shell name and no child; measured on a PTY with a bash script on the alternate screen that draws a header once, redraws on SIGWINCH and waits in `read`: started as a file with the shebang `#!/usr/bin/env bash` from bash and from fish, and as `bash <script>` from fish, it got no size change and no redraw, while the row step of commit `cf2b773` made it redraw; the same script started by path with the shebang `#!/bin/bash` has the script's file name as leader name and is stepped; measured in the browser with `clear_before_replay` on and fish as the terminal's shell: started as `bash <script>`, the header and footer such a program drew before the replay window were missing after a reconnect (1 before, 0 after, in 3 of 3), and started by path with the shebang `#!/bin/bash` they stayed (1 before and 1 after in 3 of 3); expected, not measured: the same after a page reload, and the rows stay missing until the next browser resize
- Toggle: `DEFAULTS['repaint_on_attach']` in `__init__.py` (default on), debounced 5s per terminal

**Replay query stripping** (no replies on reconnect):

On attach, terminado replays the terminal's buffered output and xterm.js answers every query in it as if it were live, so the shell receives the answers as typed text. The extension removes those queries from the replay only.

- Stripped: OSC 4/10/11/12 color queries, DA/DA2 queries, `ESC[5n`, `ESC[6n`, `ESC[?6n`, DECRQM, DECRQSS
- Queries at the very end of the replay are kept, because the program that sent them may still wait for the answer
- Live output after the attach passes every query unchanged
- Toggle: `DEFAULTS['strip_replay_queries']` in `__init__.py` (default on); `suppress_buffer_replay` takes precedence

**Clear before replay** (one copy of the history):

Before each replay the server puts cursor home, erase screen and erase scrollback in front of the replayed output, so the client's terminal is empty when the history is written. Without it the client appends the replay to what it already shows: a plain reconnect draws the history twice.

- Prefix: `ESC[H ESC[2J ESC[3J`; the replay is not changed
- If the first alternate-screen switch in the replay (modes 47, 1047, 1049) is an entry, the prefix leaves the alternate screen first; if it is a leave, the prefix enters the alternate screen after the clear
- A replay without a switch keeps the buffer type the client shows (a full-screen program that started before the replay stays on the alternate screen), but its content is cleared and only the last 1000 chunks are drawn again; the rows the program drew before that window return through the repaint on attach, so this feature depends on `repaint_on_attach`
- An empty replay buffer (a new shell that has not written yet) gets the same clear, so the new shell starts on an empty screen
- Resets no input mode (no full or soft reset): bracketed paste, mouse reporting and cursor keys survive a reconnect
- Live output after the attach gets no prefix
- Limit: after every reconnect the terminal holds only what the server replays, the last 1000 output chunks (nothing when `suppress_buffer_replay` is on); older output is dropped, also on a plain reconnect
- Toggle: `DEFAULTS['clear_before_replay']` in `__init__.py` (default on); `suppress_buffer_replay` takes precedence

**Background terminal redraw** (history at the real size):

After a page load JupyterLab gives a terminal in a background tab an 80x24 screen until its tab is shown, reports that size to the server and writes the replayed history into it. The frontend part of this extension sends no size to the server before the terminal is opened, so the PTY keeps its real size. When the terminal is first shown it reconnects once and the server replays the history into the fitted terminal.

- Only output that arrives while the tab is hidden leads to a redraw; a terminal that is visible when its output arrives, a new one included, is not reconnected
- The redraw is one more replay from the server, so it relies on replay query stripping (on by default): with `strip_replay_queries` off, old queries in the history are answered once more when the tab is first shown
- Limits that remain only when the server runs without clear before replay (an older server part, or `clear_before_replay` off): the first row of the redrawn history can start with the text that was on the cursor's line before the redraw (usually the prompt), and history printed before a program switched to the alternate screen is not drawn again while that program runs
- Limit: the redraw replaces what the terminal held with the server's replay, which is the last 1000 output chunks (nothing when `suppress_buffer_replay` is on). Output older than that, received while the tab was in the background, is dropped. With the setting "Redraw background terminals when first shown" off it stays
- Toggle: the setting "Redraw background terminals when first shown" in the Settings Editor, section "Terminal CPR Escape Fix" (default on)

## Monkey patches

The server part works by replacing attributes of upstream classes at server start, and the frontend part replaces one method of a terminal session. Each patch is a feature with its own switch (where one exists) and can be retired once upstream no longer needs it.

| Id   | Replaced attribute                                | Feature                    | Switch                                                              | Retire when                                                           |
| ---- | ------------------------------------------------- | -------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------- |
| MP-1 | `TermSocket.on_pty_read`                          | Reply filter               | none; `filter_osc_color_responses` for the bare OSC part            | the lab no longer shows terminal replies as literal text in the shell |
| MP-2 | `TermSocket.open`                                 | Replay suppression         | `suppress_buffer_replay` (default off)                              | upstream offers a setting for no replay                               |
| MP-3 | `TermSocket.open`                                 | Replay query stripping     | `strip_replay_queries` (default on)                                 | the replay no longer makes the client answer old queries              |
| MP-4 | `TermSocket.open`                                 | Clear before replay        | `clear_before_replay` (default on)                                  | the client empties its terminal before a replay                       |
| MP-5 | `TermSocket.open`                                 | Repaint on attach          | `repaint_on_attach` (default on)                                    | a client that attaches gets a full repaint of the foreground program  |
| MP-6 | `session.send` of each terminal widget (frontend) | Background terminal redraw | setting "Redraw background terminals when first shown" (default on) | JupyterLab reports no size for a terminal whose xterm is not opened   |

The register [docs/monkeypatches.md](docs/monkeypatches.md) holds for each patch the canary test, the removal steps and the upstream versions last checked.

## Requirements

- JupyterLab >= 4.0.0

## Installation

```bash
pip install jupyterlab_terminal_cpr_escape_fix
```

## Uninstall

```bash
pip uninstall jupyterlab_terminal_cpr_escape_fix
```
