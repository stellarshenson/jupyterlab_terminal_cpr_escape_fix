# jupyterlab_terminal_cpr_escape_fix

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_terminal_cpr_escape_fix/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_terminal_cpr_escape_fix/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_terminal_cpr_escape_fix.svg)](https://www.npmjs.com/package/jupyterlab_terminal_cpr_escape_fix)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-terminal-cpr-escape-fix.svg)](https://pypi.org/project/jupyterlab-terminal-cpr-escape-fix/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-terminal-cpr-escape-fix)](https://pepy.tech/project/jupyterlab-terminal-cpr-escape-fix)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)

> [!TIP]
> This fix is part of the [stellars_jupyterlab_fixes](https://github.com/stellarshenson/stellars_jupyterlab_fixes) metapackage. Install all Stellars fixes at once: `pip install stellars_jupyterlab_fixes`

> [!WARNING]
> This extension provides a workaround for a known JupyterLab/terminado issue. It will be deprecated once JupyterLab addresses this problem in a GA release. Monitor the upstream issue tracker for official fixes.

Fix the JupyterLab terminado issue where returning to an idle terminal causes cursor position report (CPR) escape sequences to appear as literal text. This is particularly noticeable with fish shell, where sequences like `[2;2R[3;1R` or `[?1;2c[>0;276;0c` appear at the prompt after reconnecting.

## How it works

When a JupyterLab terminal sits idle, the shell (especially fish) periodically queries terminal capabilities. These queries accumulate in terminado's buffer. On reconnect, the buffer drains and the responses appear as literal text because xterm.js can't process them fast enough.

This extension patches `TermSocket.on_pty_read()` server-side to filter terminal query responses before they reach the browser. It handles both ESC-prefixed sequences and bare remnants where fish shell has stripped the ESC byte.

**Filtered sequences** (terminal query responses):

- CPR - Cursor Position Report (`ESC[row;colR`)
- DA/DA2 - Device Attributes (`ESC[?...c`, `ESC[>...c`)
- DECRPM - DEC Report Mode (`ESC[?mode;value$y`)
- OSC 4/10/11/12 - Color query responses

**Preserved sequences** (functional terminal output):

- All SGR color codes, cursor movement, erase, scroll
- OSC 0 (window/tab title), OSC 7 (cwd), OSC 8 (hyperlinks)
- OSC 52 (clipboard - used by companion clipboard extension)
- OSC 133 (shell integration prompt marks)
- Bracketed paste mode, alternate screen, all DEC private modes

## Requirements

- JupyterLab >= 4.0.0

## Installation

```bash
pip install jupyterlab_terminal_cpr_escape_fix
```

## Uninstall

```bash
pip uninstall jupyterlab_terminal_cpr_escape_fix
```
