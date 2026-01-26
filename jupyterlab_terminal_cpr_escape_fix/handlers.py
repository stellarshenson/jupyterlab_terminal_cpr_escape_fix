"""Filtered terminal websocket handler."""
import logging
import re
from jupyter_server_terminals.handlers import TermSocket

# Regex patterns for escape sequences to filter
# CPR: Cursor Position Report - ESC[row;colR
# DA: Device Attributes - ESC[?...c
CPR_PATTERN = re.compile(r'\x1b\[\d+;\d+R')
DA_PATTERN = re.compile(r'\x1b\[\?[\d;]*c')

logger = logging.getLogger(__name__)


def filter_cpr_sequences(text: str) -> tuple[str, int, int]:
    """Filter CPR and DA escape sequences from terminal output.

    Returns:
        Tuple of (filtered_text, cpr_count, da_count)
    """
    cpr_matches = CPR_PATTERN.findall(text)
    da_matches = DA_PATTERN.findall(text)

    result = CPR_PATTERN.sub('', text)
    result = DA_PATTERN.sub('', result)

    return result, len(cpr_matches), len(da_matches)


class CPRFilteredTermSocket(TermSocket):
    """Terminal websocket that filters CPR escape sequences.

    When a client reconnects to an existing terminal, terminado drains
    the accumulated read_buffer and sends it as bulk text. CPR sequences
    (ESC[row;colR) embedded in this bulk data render as literal text
    instead of being processed by xterm.js.

    This handler filters those sequences in on_pty_read() before they
    reach the frontend.
    """

    def on_pty_read(self, text: str) -> None:
        """Filter CPR sequences before sending to frontend."""
        filtered, cpr_count, da_count = filter_cpr_sequences(text)

        if cpr_count > 0 or da_count > 0:
            logger.info(
                "CPR filter: intercepted %d CPR and %d DA sequences from buffer drain",
                cpr_count,
                da_count
            )

        super().on_pty_read(filtered)
