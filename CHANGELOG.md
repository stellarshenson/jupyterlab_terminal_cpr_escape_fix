# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

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
