# logs/

Background job and release logs for this project. All background jobs tee their
output here per workspace policy.

- `release-1.0.10.log` - `make publish` output for the v1.0.10 release
- `release-1.0.11.log` - `make publish` output for the v1.0.11 release
- `release-1.0.12.log` - `make publish` output for the v1.0.12 release
- `terminal-signal-recorder.log` - progress log of the detached WebSocket signal
  recorder probing terminal/status-line disruption on window refresh
  (frames data in `/tmp/wsrecorder/`)
- `ui-tests-<run>.log` - Playwright/Galata run output of `ui-tests`, one file per run
- `pytest-<run>.log` - pytest run output of the server extension tests
- `lint-<run>.log` - `jlpm run lint:check` output
- `install-<n>.log` - `make install` output
- `jest-<run>.log` - `make test` output of the frontend unit tests
- `labextension-<run>.log` - `jupyter labextension list` output
- `e5-<arm>-<cell>[-bash]-<port>.log`, `e5-queue-*.log` - Galata output of experiment E5 (`tmp/research/e5/`), one file per arm and cell
- `verify-bounce-<pytest|jest|lint|galata-<shell>|mutations-pytest|probe-<shell>|m6>[-<port>].log` - verifier runs of the column-step and clear-before-replay changes (`tmp/research/bounce-verify/`)
- `review3-<bh|ux|fix|fix2>-<run>[-<port>].log` - runs of review round 3 and of its fix rounds (`tmp/research/review3/`)
