"""Filtered terminal websocket handler."""
import logging
import re
from jupyter_server_terminals.handlers import TermSocket

# Regex patterns for terminal query responses to filter
# These are responses the terminal sends back to the shell in reply to queries.
# When accumulated in terminado's buffer and replayed on reconnect, they render
# as literal text instead of being processed.
#
# CPR: Cursor Position Report - ESC[row;colR
# DA: Device Attributes - ESC[?...c
# DA2: Secondary Device Attributes - ESC[>...c
# DECRPM: DEC Report Mode - ESC[?mode;value$y
# OSC responses: ESC]N;...ST where ST is ESC\ or BEL
#   OSC 10: foreground color  ESC]10;rgb:RRRR/GGGG/BBBB ESC\
#   OSC 11: background color  ESC]11;rgb:RRRR/GGGG/BBBB ESC\
#   OSC 4:  color palette     ESC]4;N;rgb:RRRR/GGGG/BBBB ESC\
CPR_PATTERN = re.compile(r'\x1b\[\d+;\d+R')
DA_PATTERN = re.compile(r'\x1b\[\?[\d;]*c')
DA2_PATTERN = re.compile(r'\x1b\[>[\d;]*c')
DECRPM_PATTERN = re.compile(r'\x1b\[\??\d+;\d+\$y')
OSC_RESPONSE_PATTERN = re.compile(r'\x1b\]\d+;[^\x07\x1b]*(?:\x07|\x1b\\)')

# Debug: pattern to find any escape sequences for logging
ANY_CSI_PATTERN = re.compile(r'\x1b\[[0-9;?>]*[a-zA-Z$][a-zA-Z]?')
ANY_OSC_PATTERN = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)')

logger = logging.getLogger(__name__)

# All filter patterns with their names
FILTER_PATTERNS = [
    ('cpr', CPR_PATTERN),
    ('da', DA_PATTERN),
    ('da2', DA2_PATTERN),
    ('decrpm', DECRPM_PATTERN),
    ('osc', OSC_RESPONSE_PATTERN),
]


def filter_terminal_responses(text: str) -> tuple[str, dict[str, int]]:
    """Filter terminal query responses from output.

    Returns:
        Tuple of (filtered_text, counts_dict)
    """
    counts = {}
    result = text

    for name, pattern in FILTER_PATTERNS:
        matches = pattern.findall(result)
        counts[name] = len(matches)
        if matches:
            result = pattern.sub('', result)

    return result, counts


def debug_escape_sequences(text: str) -> list[str]:
    """Find all escape sequences in text for debugging."""
    csi = ANY_CSI_PATTERN.findall(text)
    osc = ANY_OSC_PATTERN.findall(text)
    return csi + osc


class CPRFilteredTermSocket(TermSocket):
    """Terminal websocket that filters terminal query responses.

    When a client reconnects to an existing terminal, terminado drains
    the accumulated read_buffer and sends it as bulk text. Terminal
    query responses (CPR, DA, DECRPM, OSC color queries) embedded in
    this bulk data render as literal text instead of being processed.

    This handler filters those sequences in on_pty_read() before they
    reach the frontend.
    """

    def on_pty_read(self, text: str) -> None:
        """Filter terminal query responses before sending to frontend."""
        # Debug: log ALL escape sequences for diagnostics
        escapes = debug_escape_sequences(text)
        if escapes:
            logger.info(
                "CPR filter: buffer (%d bytes) contains %d escape sequences: %r",
                len(text),
                len(escapes),
                escapes[:20] if len(escapes) > 20 else escapes
            )

        filtered, counts = filter_terminal_responses(text)

        total_filtered = sum(counts.values())
        if total_filtered > 0:
            active = {k: v for k, v in counts.items() if v > 0}
            logger.info(
                "CPR filter: FILTERED %d sequences: %s",
                total_filtered,
                ', '.join(f'{v} {k}' for k, v in active.items())
            )

        super().on_pty_read(filtered)
