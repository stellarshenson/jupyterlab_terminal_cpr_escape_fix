"""JupyterLab extension to fix CPR escape sequences in terminals."""

import os

DEFAULTS = {
    'suppress_buffer_replay': False,
    'filter_osc_color_responses': True,
    'repaint_on_attach': True,
    'strip_replay_queries': True,
    'clear_before_replay': True,
}

# repaint_on_attach tuning: after a client attaches and the buffer replay drains,
# set the PTY one column narrower and back so the kernel delivers SIGWINCH and
# the foreground app repaints its full screen - without this, static regions
# (Claude Code status line, input box) stay missing on the fresh client because
# the replay window only holds incremental diff frames.
# A column step, not a row step: a program that addresses rows absolutely in the
# normal buffer (Codex-like) takes the taller PTY as truth, writes one row below
# the browser's last row, and the line it commits during the step is lost
# (DEF-BOUNCE-14). A column step moves no row. One column narrower, not wider: a
# program that writes to the last column wraps when the PTY is wider than the
# browser (E4 audit: 16 of 16 damaged with cols + 1, 0 of 16 with cols - 1).
# No step while the foreground process group of the terminal is one shell alone,
# which the server treats as a shell at its prompt (_shell_at_prompt): a width
# step makes a line editor miscount the rows of a typed line that fills the
# width, so it erases the output line above the prompt, and a shell at its prompt
# needs no repaint because the replay restores its line. A shell with a child in
# its own process group is stepped: it runs a program without job control
# (sh -c "<program>; true", bash <script>), and that program needs the repaint.
# A line editor that is not one of the shells in _SHELLS is still stepped. On a
# system without /proc/<pid>/task/<pid>/children the step always runs.
_BOUNCE_DELAY = 0.4   # let client geometry settle before the bounce
_BOUNCE_STEP = 0.12   # pause between the narrow and the restore write
_BOUNCE_DEBOUNCE = 5.0  # min seconds between bounces on the same terminal
_SHELLS = frozenset({b'bash', b'sh', b'dash', b'zsh', b'fish', b'ksh', b'tcsh', b'csh'})


def _shell_at_prompt(term):
    """Return True when the foreground process group of the PTY is one shell alone.

    The server treats that as a shell at its prompt. The leader is a shell when the
    bytes of /proc/<leader>/comm are in `_SHELLS`; it is alone when no child in
    /proc/<leader>/task/<leader>/children has the leader's process group.
    False for a shell with a child in its own group: it runs a program without
    job control, and that program needs the repaint. A child in another group
    (a background job) does not count. False when the state cannot be read: a
    terminal without `fd`, no /proc, no children file, a process that exited.
    """
    try:
        leader = os.tcgetpgrp(term.fd)
        with open(f'/proc/{leader}/comm', 'rb') as comm:
            if comm.read().strip() not in _SHELLS:
                return False
        with open(f'/proc/{leader}/task/{leader}/children', 'rb') as children:
            return all(os.getpgid(int(pid)) != leader for pid in children.read().split())
    except (AttributeError, OSError):
        return False


def _make_winsize_bounce(term, schedule):
    """Return a function that sets a PTY one column narrower and back.

    Each size change makes the kernel send SIGWINCH to the foreground process
    group, which makes TUI apps (Claude Code, vim, htop) repaint their full
    screen. The restore write is guarded: it only runs if the size is still the
    bounced one, so a real client resize racing the bounce is never clobbered.
    `schedule(delay, fn)` abstracts the IOLoop so the logic stays testable.
    The function does nothing while the foreground process group is one shell
    alone (`_shell_at_prompt`).

    Known limitation: the guard treats any size equal to the bounced size as
    bounce-written, so a real client resize to exactly cols-1 within the step
    window is reverted and the PTY is one column wider than that client until
    the next resize event.
    """
    def bounce():
        if _shell_at_prompt(term):
            return
        try:
            rows, cols = term.getwinsize()
            term.setwinsize(rows, cols - 1)
        except Exception:
            return

        def restore():
            try:
                if term.getwinsize() == (rows, cols - 1):
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
    from .handlers import filter_terminal_responses, FILTER_PATTERNS, strip_replay_queries
    from .replay_clear import clear_before_replay

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

        if DEFAULTS['suppress_buffer_replay'] or DEFAULTS['repaint_on_attach'] or DEFAULTS['strip_replay_queries'] or DEFAULTS['clear_before_replay']:
            from tornado.ioloop import IOLoop

            _original_open = TermSocket.open
            _last_bounce = {}  # terminal name -> monotonic time of last bounce

            def _replay_steps(text):
                if DEFAULTS['strip_replay_queries']:
                    text = strip_replay_queries(text)
                if DEFAULTS['clear_before_replay']:
                    text = clear_before_replay(text)
                return text

            def _patched_open(self, url_component=None):
                replays = []  # the replay texts the original open handed to the hook
                if DEFAULTS['suppress_buffer_replay']:
                    self.on_pty_read = lambda text: None
                elif DEFAULTS['strip_replay_queries'] or DEFAULTS['clear_before_replay']:
                    def replay(text):
                        replays.append(text)
                        # the replay still goes through the response filter on the class
                        type(self).on_pty_read(self, _replay_steps(text))
                    self.on_pty_read = replay
                _original_open(self, url_component)
                if DEFAULTS['clear_before_replay'] and not DEFAULTS['suppress_buffer_replay'] and not replays:
                    # an empty buffer skips the hook (terminado replays only a non-empty
                    # buffer); clear anyway, so a new shell starts on an empty screen
                    type(self).on_pty_read(self, clear_before_replay(''))
                if DEFAULTS['suppress_buffer_replay'] or DEFAULTS['strip_replay_queries'] or DEFAULTS['clear_before_replay']:
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
            elif DEFAULTS['strip_replay_queries']:
                patches.append('replay query stripping')
            if DEFAULTS['clear_before_replay'] and not DEFAULTS['suppress_buffer_replay']:
                patches.append('clear before replay')
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
