# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

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
