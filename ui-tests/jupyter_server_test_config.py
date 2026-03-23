"""Server configuration for integration tests.

!! Never use this configuration in production because it
opens the server to the world and provide access to JupyterLab
JavaScript objects through the global window variable.
"""
from jupyterlab.galata import configure_jupyter_server

configure_jupyter_server(c)

# Disable heavy extensions to speed up test server startup
c.ServerApp.jpserver_extensions = {
    "jupyterlab": True,
    "jupyterlab_terminal_cpr_escape_fix": True,
    "jupyter_server_terminals": True,
}

# Uncomment to set server log level to debug level
# c.ServerApp.log_level = "DEBUG"
