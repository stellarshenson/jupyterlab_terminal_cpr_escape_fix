"""Server configuration for integration tests.

!! Never use this configuration in production because it
opens the server to the world and provide access to JupyterLab
JavaScript objects through the global window variable.
"""
import json
import os
import re
import shlex
import sys
import time

from jupyterlab.galata import configure_jupyter_server

configure_jupyter_server(c)

# Galata pins port 8888 with port_retries = 0; 8888 is the developer's own lab.
# `or`, not a get() default: an exported-but-empty value would make int("")
# raise while Playwright waited on the default.
c.ServerApp.port = int(os.environ.get("JUPYTER_TEST_PORT") or "8899")

# Disable heavy extensions to speed up test server startup
c.ServerApp.jpserver_extensions = {
    "jupyterlab": True,
    "jupyterlab_terminal_cpr_escape_fix": True,
    "jupyter_server_terminals": True,
}

# Delete outright: galata removes each test's folder through the contents API,
# and jupyter_server's default delete_to_trash=True has no trash to write to under /tmp.
c.FileContentsManager.delete_to_trash = False
c.AsyncFileContentsManager.delete_to_trash = False
c.AsyncLargeFileManager.delete_to_trash = False
c.AsyncJupytextContentsManager.delete_to_trash = False

# The shell the user's lab runs, not galata's bash with PS1="$ ". A runner
# without fish (the CI image) keeps galata's bash.
_SHELL = os.environ.get("TEST_TERMINAL_SHELL") or (
    "/usr/bin/fish --login" if os.path.exists("/usr/bin/fish") else ""
)
if _SHELL:
    c.ServerApp.terminado_settings = {"shell_command": shlex.split(_SHELL)}
print(f"terminal shell: {c.ServerApp.terminado_settings['shell_command']}", file=sys.stderr)

# The server extension under test must be the working tree (playwright.config.js
# puts it on PYTHONPATH), not the installed copy in site-packages. This config
# runs before the extension loads, so the module imported here is the one the
# server uses.
import jupyterlab_terminal_cpr_escape_fix as cpr_fix  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PACKAGE = os.path.dirname(os.path.abspath(cpr_fix.__file__))
if _PACKAGE != os.path.join(_REPO, "jupyterlab_terminal_cpr_escape_fix"):
    raise RuntimeError(f"cpr-fix imported from {_PACKAGE}, not the working tree {_REPO}")
# stderr: playwright's webServer ignores the server's stdout
print(f"cpr-fix package under test: {_PACKAGE}", file=sys.stderr)

# CPR_FIX_DEFAULTS='{"repaint_on_attach": false}' toggles the extension before it
# reads DEFAULTS at load time. An unknown key is a typo that would otherwise run
# the experiment on the default and report it as the toggled one.
_overrides = json.loads(os.environ.get("CPR_FIX_DEFAULTS") or "{}")
_unknown = set(_overrides) - set(cpr_fix.DEFAULTS)
if _unknown:
    raise ValueError(f"CPR_FIX_DEFAULTS has unknown keys {sorted(_unknown)}; known: {sorted(cpr_fix.DEFAULTS)}")
cpr_fix.DEFAULTS.update(_overrides)
print(f"cpr-fix DEFAULTS: {cpr_fix.DEFAULTS}", file=sys.stderr)

# Terminal watch (test-only): TERMINAL_WATCH_FILE=<path> appends one JSON line
# per server-side terminal event - open, each client message (stdin, set_size),
# each PTY resize (setwinsize), and the buffer replayed to an attaching client.
# The wrappers are installed on the classes before the extension loads, so the
# extension wraps them in turn: its open() runs outside this one, and its bounce
# resize is recorded as a setwinsize.
_WATCH_FILE = os.environ.get("TERMINAL_WATCH_FILE")
if _WATCH_FILE:
    import ptyprocess
    from jupyter_server_terminals.handlers import TermSocket

    # Terminal queries - sequences that make xterm.js write a response back
    # into the PTY when they are replayed to a fresh client.
    _QUERIES = {
        "osc4_q": re.compile(r"\x1b\]4;[^\x07\x1b]*\?(?:\x07|\x1b\\)"),
        "osc10_q": re.compile(r"\x1b\]10;\?(?:\x07|\x1b\\)"),
        "osc11_q": re.compile(r"\x1b\]11;\?(?:\x07|\x1b\\)"),
        "osc12_q": re.compile(r"\x1b\]12;\?(?:\x07|\x1b\\)"),
        "da1_c": re.compile(r"\x1b\[c"),
        "da1_0c": re.compile(r"\x1b\[0c"),
        "da2_gt_c": re.compile(r"\x1b\[>0?c"),
        "dsr_5n": re.compile(r"\x1b\[5n"),
        "cpr_6n": re.compile(r"\x1b\[6n"),
        "decxcpr_q6n": re.compile(r"\x1b\[\?6n"),
        "decrqm_q_p": re.compile(r"\x1b\[\?\d+\$p"),
        "decrqss_dcs_q": re.compile(r"\x1bP\$q"),
        "xtwinops_14t": re.compile(r"\x1b\[14t"),
        "xtwinops_16t": re.compile(r"\x1b\[16t"),
        "xtwinops_18t": re.compile(r"\x1b\[18t"),
        "xtversion_gt_q": re.compile(r"\x1b\[>0?q"),
        "kitty_kbd_q_u": re.compile(r"\x1b\[\?u"),
    }
    # ptyproc -> terminal name, filled on open; the spawn-time resize comes
    # before any open and is recorded with term null - match it by pid
    _pty_names = {}

    def _watch(term, event, **fields):
        line = json.dumps({"t": round(time.time() * 1000, 1), "term": term, "event": event, **fields})
        with open(_WATCH_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    _inner_open = TermSocket.open

    def _watched_open(self, url_component=None):
        name = url_component or "tty"
        terminal = self.term_manager.terminals.get(name)
        buffered = "".join(terminal.read_buffer) if terminal else ""
        _inner_open(self, url_component)
        _pty_names[id(self.terminal.ptyproc)] = self.term_name
        _watch(self.term_name, "open", pid=self.terminal.ptyproc.pid, clients=len(self.terminal.clients))
        if buffered:
            counts = {k: len(p.findall(buffered)) for k, p in _QUERIES.items()}
            _watch(
                self.term_name,
                "replay",
                len=len(buffered),
                replay_query_counts={k: v for k, v in counts.items() if v},
                suppressed=cpr_fix.DEFAULTS["suppress_buffer_replay"],
            )

    _inner_on_message = TermSocket.on_message

    async def _watched_on_message(self, message):
        command = json.loads(message)
        if command[0] == "stdin":
            _watch(self.term_name, "stdin", data=command[1])
        elif command[0] == "set_size":
            _watch(self.term_name, "set_size", rows=command[1], cols=command[2])
        else:
            _watch(self.term_name, command[0], data=command[1:])
        await _inner_on_message(self, message)

    _inner_setwinsize = ptyprocess.PtyProcess.setwinsize

    def _watched_setwinsize(self, rows, cols):
        _watch(_pty_names.get(id(self)), "setwinsize", pid=self.pid, rows=rows, cols=cols)
        return _inner_setwinsize(self, rows, cols)

    TermSocket.open = _watched_open
    TermSocket.on_message = _watched_on_message
    ptyprocess.PtyProcess.setwinsize = _watched_setwinsize
    print(f"terminal watch writing to: {_WATCH_FILE}", file=sys.stderr)

# Uncomment to set server log level to debug level
# c.ServerApp.log_level = "DEBUG"
