"""JupyterLab extension to fix CPR escape sequences in terminals."""
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
    from .handlers import filter_terminal_responses

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

        server_app.log.info(
            "jupyterlab_terminal_cpr_escape_fix: Patched TermSocket.on_pty_read with CPR filter"
        )
    except ImportError:
        server_app.log.warning(
            "jupyterlab_terminal_cpr_escape_fix: jupyter_server_terminals not found"
        )
