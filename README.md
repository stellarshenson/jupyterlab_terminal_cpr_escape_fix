# jupyterlab_terminal_cpr_escape_fix

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_terminal_cpr_escape_fix/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_terminal_cpr_escape_fix/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_terminal_cpr_escape_fix.svg)](https://www.npmjs.com/package/jupyterlab_terminal_cpr_escape_fix)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-terminal-cpr-escape-fix.svg)](https://pypi.org/project/jupyterlab-terminal-cpr-escape-fix/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-terminal-cpr-escape-fix)](https://pepy.tech/project/jupyterlab-terminal-cpr-escape-fix)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)

> [!WARNING]
> This extension provides a workaround for a known JupyterLab/terminado issue. It will be deprecated once JupyterLab addresses this problem in a GA release. Monitor the upstream issue tracker for official fixes.

Fix the JupyterLab terminado issue where returning to an idle terminal causes cursor position report (CPR) escape sequences to appear as literal text.

## Features

- **CPR escape sequence handling** - Intercepts and processes CPR sequences that would otherwise appear as `^[[6n` or similar garbage text
- **Server-side processing** - Python backend handles terminal state management
- **Automatic activation** - Extension activates on JupyterLab startup with no configuration required

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
