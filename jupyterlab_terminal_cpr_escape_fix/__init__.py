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
    from .handlers import CPRFilteredTermSocket

    # Monkey-patch the TermSocket class before any terminals are created
    # This must happen early, before jupyter_server_terminals initializes handlers
    try:
        from jupyter_server_terminals import handlers as term_handlers
        term_handlers.TermSocket = CPRFilteredTermSocket
        server_app.log.info(
            "jupyterlab_terminal_cpr_escape_fix: Installed CPR filter on TermSocket"
        )
    except ImportError:
        server_app.log.warning(
            "jupyterlab_terminal_cpr_escape_fix: jupyter_server_terminals not found"
        )
