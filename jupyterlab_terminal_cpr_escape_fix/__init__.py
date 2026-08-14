"""JupyterLab extension to fix CPR escape sequences in terminals."""

DEFAULTS = {
    'suppress_buffer_replay': False,
    'filter_osc_color_responses': True,
    'repaint_on_attach': True,
}

# repaint_on_attach tuning: after a client attaches and the buffer replay drains,
# bounce the PTY one row taller and back so the kernel delivers SIGWINCH and the
# foreground app repaints its full screen - without this, static regions (Claude
# Code status line, input box) stay missing on the fresh client because the
# replay window only holds incremental diff frames.
_BOUNCE_DELAY = 0.4   # let client geometry settle before the bounce
_BOUNCE_STEP = 0.12   # pause between the grow and the restore write
_BOUNCE_DEBOUNCE = 5.0  # min seconds between bounces on the same terminal


def _make_winsize_bounce(term, schedule):
    """Return a function that nudges a PTY one row taller and back.

    Each size change makes the kernel send SIGWINCH to the foreground process
    group, which makes TUI apps (Claude Code, vim, htop) repaint their full
    screen. The restore write is guarded: it only runs if the size is still the
    bounced one, so a real client resize racing the bounce is never clobbered.
    `schedule(delay, fn)` abstracts the IOLoop so the logic stays testable.

    Known limitation: the guard treats any size equal to the bounced size as
    bounce-written, so a real client resize to exactly rows+1 within the step
    window is reverted and the PTY sits one row short until the next resize
    event self-heals it.
    """
    def bounce():
        try:
            rows, cols = term.getwinsize()
            term.setwinsize(rows + 1, cols)
        except Exception:
            return

        def restore():
            try:
                if term.getwinsize() == (rows + 1, cols):
                    term.setwinsize(rows, cols)
            except Exception:
                pass

        schedule(_BOUNCE_STEP, restore)
    return bounce
try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode:
    # https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'jupyterlab_terminal_cpr_escape_fix' outside a proper installation.")
    __version__ = "dev"


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyterlab_terminal_cpr_escape_fix"
    }]


def _jupyter_server_extension_points():
    return [{
        "module": "jupyterlab_terminal_cpr_escape_fix"
    }]


def _load_jupyter_server_extension(server_app):
    """Register the CPR-filtered terminal handler.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    from .handlers import filter_terminal_responses, FILTER_PATTERNS

    # bare_osc is in FILTER_PATTERNS by default; drop it when the toggle is off
    # so the bare OSC color-response filter can be disabled without code change.
    if not DEFAULTS['filter_osc_color_responses']:
        FILTER_PATTERNS[:] = [p for p in FILTER_PATTERNS if p[0] != 'bare_osc']

    # Patch on_pty_read directly on the TermSocket class.
    # Replacing the module attribute doesn't work because jupyter_server_terminals
    # registers its URL handler with the original TermSocket class reference
    # before our extension loads. We must patch the class method itself.
    try:
        from jupyter_server_terminals.handlers import TermSocket

        import logging
        import time
        from collections import Counter

        _original_on_pty_read = TermSocket.on_pty_read
        _logger = logging.getLogger('jupyterlab_terminal_cpr_escape_fix.handlers')
        _LOG_INTERVAL = 60  # seconds
        _accum = {'counts': Counter(), 'matched': [], 'last_flush': time.monotonic()}

        def _flush_log():
            if _accum['counts']:
                active = {k: v for k, v in _accum['counts'].items() if v > 0}
                unique = sorted(set(_accum['matched']))
                _logger.info(
                    "CPR filter: FILTERED %d sequences in last %ds: %s | %r",
                    sum(_accum['counts'].values()),
                    _LOG_INTERVAL,
                    ', '.join(f'{v} {k}' for k, v in active.items()),
                    unique
                )
            _accum['counts'] = Counter()
            _accum['matched'] = []
            _accum['last_flush'] = time.monotonic()

        def _filtered_on_pty_read(self, text):
            filtered, counts, matched = filter_terminal_responses(text)
            total = sum(counts.values())
            if total > 0:
                _accum['counts'].update({k: v for k, v in counts.items() if v > 0})
                _accum['matched'].extend(matched)
            if time.monotonic() - _accum['last_flush'] >= _LOG_INTERVAL:
                _flush_log()
            _original_on_pty_read(self, filtered)

        TermSocket.on_pty_read = _filtered_on_pty_read

        patches = ['CPR filter']

        if DEFAULTS['suppress_buffer_replay'] or DEFAULTS['repaint_on_attach']:
            from tornado.ioloop import IOLoop

            _original_open = TermSocket.open
            _last_bounce = {}  # terminal name -> monotonic time of last bounce

            def _patched_open(self, url_component=None):
                if DEFAULTS['suppress_buffer_replay']:
                    self.on_pty_read = lambda text: None
                _original_open(self, url_component)
                if DEFAULTS['suppress_buffer_replay']:
                    try:
                        del self.on_pty_read
                    except AttributeError:
                        pass
                if DEFAULTS['repaint_on_attach']:
                    key = self.term_name
                    now = time.monotonic()
                    if now - _last_bounce.get(key, -_BOUNCE_DEBOUNCE) >= _BOUNCE_DEBOUNCE:
                        # entries aged past the debounce window are inert; prune in place
                        for stale in [k for k, ts in _last_bounce.items() if now - ts >= _BOUNCE_DEBOUNCE]:
                            del _last_bounce[stale]
                        _last_bounce[key] = now
                        IOLoop.current().call_later(
                            _BOUNCE_DELAY,
                            _make_winsize_bounce(self.terminal.ptyproc, IOLoop.current().call_later)
                        )

            TermSocket.open = _patched_open
            if DEFAULTS['suppress_buffer_replay']:
                patches.append('buffer replay suppression')
            if DEFAULTS['repaint_on_attach']:
                patches.append('repaint on attach')

        server_app.log.info(
            "jupyterlab_terminal_cpr_escape_fix: Patched TermSocket — %s",
            ', '.join(patches)
        )
    except ImportError:
        server_app.log.warning(
            "jupyterlab_terminal_cpr_escape_fix: jupyter_server_terminals not found"
        )
