# logs/

Background job and release logs for this project. All background jobs tee their
output here per workspace policy.

- `release-1.0.10.log` - `make publish` output for the v1.0.10 release
- `release-1.0.11.log` - `make publish` output for the v1.0.11 release
- `release-1.0.12.log` - `make publish` output for the v1.0.12 release
- `terminal-signal-recorder.log` - progress log of the detached WebSocket signal
  recorder probing terminal/status-line disruption on window refresh
  (frames data in `/tmp/wsrecorder/`)
