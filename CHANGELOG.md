# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## [1.0.20] - 2026-10-12

### Changed

- No change in code, tests or documents since 1.0.19; this version publishes the same content again

## [1.0.19] - 2026-10-12

### Added

- Clear before replay - before each history replay the server puts cursor home, erase screen and erase scrollback in front of the replayed output, so the terminal holds the history once after a reconnect; no input mode is reset, and an empty replay buffer gets the same clear
- `DEFAULTS['clear_before_replay']` toggle (default on); `suppress_buffer_replay` takes precedence
- Shell guard for the repaint on attach - no size step while the foreground process group of the terminal is one shell alone (bash, sh, dash, zsh, fish, ksh, tcsh, csh)
- Monkey patch register `docs/monkeypatches.md` and README section "Monkey patches" - for each of the six patches the replaced attribute, the switch, the canary test, the retire condition and the removal steps
- Mock-based pytest cases for the clear and for the repaint step, and Galata specs `ui-tests/tests/replay-clear.spec.ts` and `ui-tests/tests/repaint-on-attach.spec.ts`, runnable with fish or bash

### Changed

- Repaint on attach sets the PTY one column narrower for 0.12 s, in place of one row taller
- README lists the limits of the clear and of the repaint step: after every reconnect the terminal holds only the last 1000 output chunks, a line editor that is not one of the eight shells is still stepped, and a full-screen program that is itself a shell script gets no step

### Fixed

- A plain reconnect drew the terminal history twice
- The redraw of a background terminal kept the old cursor row, and history printed before an alternate-screen program was not drawn again
- A program that addresses rows absolutely on the normal buffer lost the line it committed during the repaint step

## [1.0.18] - 2026-10-12

### Added

- Background terminal redraw - after a page load a terminal in a background tab sends no size to the server before it is opened, so its PTY keeps its real size, and it reconnects once when first shown, so its history is drawn again at the fitted size instead of the 80x24 layout JupyterLab gives an unopened terminal
- Setting "Redraw background terminals when first shown" in the Settings Editor, section "Terminal CPR Escape Fix" (default on)
- Jest unit tests for the frontend module and Galata regression spec `ui-tests/tests/background-terminal.spec.ts`, runnable with fish or bash

### Changed

- Galata test server uses a private settings directory and turns off the startup tab of the GalaxaHub message-of-the-day extension, which had made every Galata test time out
- `junit.xml` is gitignored and `tmp/` is excluded from ESLint
- README lists the limits of the redraw: the first row can start with the old cursor line, history printed before an alternate-screen program is not drawn again, and output older than the server's last 1000 chunks is dropped

### Fixed

- After a page reload, programs in a background tab ran at 80 columns until the tab was shown
- After a page reload, history drawn with cursor movement was laid out for 80 columns in a background tab and stayed so once the tab was shown: stacked prompt rows in fish, stacked frames in Codex

## [1.0.15] - 2026-09-24

### Added

- Replay query stripping - terminal queries (OSC 4/10/11/12 colour queries including chained forms, DA1, DA2, `ESC[5n`, `ESC[6n`, `ESC[?6n`, DECRQM, DECRQSS) are removed from the buffer replay terminado sends on attach, so a page reload or reconnect no longer makes the browser answer old queries into the shell; queries at the very end of the replay are kept and live output is untouched
- `DEFAULTS['strip_replay_queries']` toggle (default on); `suppress_buffer_replay` takes precedence
- Galata regression spec `ui-tests/tests/replay-queries.spec.ts` counting reply frames after drops, reconnects and reloads, runnable with fish or bash

### Changed

- Galata harness moved to galata 5.6.3 with a configurable test port (`JUPYTER_TEST_PORT`), the working-tree package on `PYTHONPATH`, and an optional terminal frame watch
- Acceptance criteria and defects are tracked with pm-tools in `docs/acc-crit.md` and `docs/defects.md`; observed effects moved to `docs/observed-effects.md`
- README states the proven cause of the replayed replies

### Fixed

- The output filter deleted the live OSC 4 palette query `ESC]4;n;?`, so programs asking for palette colours waited for their timeout

## [1.0.14] - 2026-08-14

### Changed

- Documentation-only release: changelog history seeded and the repaint-on-attach investigation recorded in the journal; no change to the published extension code

## [1.0.13] - 2026-08-14

### Added

- Repaint on attach - after a client attaches and the terminado buffer replay drains, the PTY winsize is nudged one row and restored so SIGWINCH forces the foreground app to repaint its full screen, restoring status lines and input boxes lost on a browser refresh
- `DEFAULTS['repaint_on_attach']` toggle (default on) gating the new behaviour
- Regression tests pinning the loader wiring, the debounce window and the in-place prune of inert debounce entries

### Fixed

- Bounce reached terminado's `PtyWithClients` wrapper, which exposes no winsize API, making the repaint a silent no-op; it now targets the underlying `ptyproc`
- Debounce keyed off a raw URL component with an unreachable `id(self)` fallback; it now uses the canonical `term_name` the terminal manager owns
- `_last_bounce` grew unbounded across terminal names; entries aged past the debounce window are pruned in place

<!-- <END NEW CHANGELOG ENTRY> -->
