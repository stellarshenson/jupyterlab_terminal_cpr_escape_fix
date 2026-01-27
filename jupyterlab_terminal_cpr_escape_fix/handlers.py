"""Filtered terminal websocket handler."""
import logging
import re
from jupyter_server_terminals.handlers import TermSocket

# Regex patterns for escape sequences to filter
# CPR: Cursor Position Report - ESC[row;colR
# DA: Device Attributes - ESC[?...c
# DA2: Secondary Device Attributes - ESC[>...c
# DECRPM: DEC Report Mode - ESC[mode;value$y
CPR_PATTERN = re.compile(r'\x1b\[\d+;\d+R')
DA_PATTERN = re.compile(r'\x1b\[\?[\d;]*c')
DA2_PATTERN = re.compile(r'\x1b\[>[\d;]*c')
DECRPM_PATTERN = re.compile(r'\x1b\[\??\d+;\d+\$y')

# Debug: pattern to find any escape sequences for logging
# Extended to catch $y terminated sequences
ANY_CSI_PATTERN = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z$][a-zA-Z]?')
ANY_OSC_PATTERN = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)')

logger = logging.getLogger(__name__)


def filter_cpr_sequences(text: str) -> tuple[str, dict[str, int]]:
    """Filter CPR, DA, and DECRPM escape sequences from terminal output.

    Returns:
        Tuple of (filtered_text, counts_dict)
    """
    counts = {
        'cpr': len(CPR_PATTERN.findall(text)),
        'da': len(DA_PATTERN.findall(text)),
        'da2': len(DA2_PATTERN.findall(text)),
        'decrpm': len(DECRPM_PATTERN.findall(text)),
    }

    result = CPR_PATTERN.sub('', text)
    result = DA_PATTERN.sub('', result)
    result = DA2_PATTERN.sub('', result)
    result = DECRPM_PATTERN.sub('', result)

    return result, counts


def debug_escape_sequences(text: str) -> list[str]:
    """Find all escape sequences in text for debugging."""
    csi = ANY_CSI_PATTERN.findall(text)
    osc = ANY_OSC_PATTERN.findall(text)
    return csi + osc


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
        # Debug: log ALL escape sequences for diagnostics
        escapes = debug_escape_sequences(text)
        if escapes:
            logger.info(
                "CPR filter: buffer (%d bytes) contains %d escape sequences: %r",
                len(text),
                len(escapes),
                escapes[:20] if len(escapes) > 20 else escapes
            )

        filtered, counts = filter_cpr_sequences(text)

        total_filtered = sum(counts.values())
        if total_filtered > 0:
            logger.info(
                "CPR filter: FILTERED %d CPR, %d DA, %d DA2, %d DECRPM sequences",
                counts['cpr'],
                counts['da'],
                counts['da2'],
                counts['decrpm']
            )

        super().on_pty_read(filtered)
