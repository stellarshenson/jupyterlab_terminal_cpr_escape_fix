"""Filtered terminal websocket handler.

Filters terminal query responses that appear as literal text when
reconnecting to idle terminals. Fish shell (and others) strip the ESC
byte from responses and echo the remainder as bare text, so we filter
both ESC-prefixed and bare patterns.
"""
import logging
import re

# Patterns WITH ESC prefix (standard terminal responses)
ESC_CPR = re.compile(r'\x1b\[\d+;\d+R')
ESC_DA = re.compile(r'\x1b\[\?[\d;]*c')
ESC_DA2 = re.compile(r'\x1b\[>[\d;]*c')
ESC_DECRPM = re.compile(r'\x1b\[\??\d+;\d+\$y')
# Only filter OSC color query responses (4, 10, 11, 12), not commands like
# OSC 0 (window title), OSC 7 (cwd), OSC 8 (hyperlinks), OSC 52 (clipboard)
ESC_OSC = re.compile(r'\x1b\](?:4|10|11|12);[^\x07\x1b]*(?:\x07|\x1b\\)')

# Patterns WITHOUT ESC prefix (bare remnants after shell strips ESC)
# Fish shell receives ESC[row;colR, strips ESC, outputs [row;colR
# These use negative lookbehind to avoid matching ESC-prefixed sequences twice
BARE_CPR = re.compile(r'(?<!\x1b)\[\d+;\d+R')
BARE_DA = re.compile(r'(?<!\x1b)\[\?[\d;]*c')
BARE_DA2 = re.compile(r'(?<!\x1b)\[>[\d;]*c')
BARE_DECRPM = re.compile(r'(?<!\x1b)\[\??\d+;\d+\$y')

logger = logging.getLogger(__name__)

# All filter patterns: ESC-prefixed first, then bare remnants
FILTER_PATTERNS = [
    ('cpr', ESC_CPR),
    ('da', ESC_DA),
    ('da2', ESC_DA2),
    ('decrpm', ESC_DECRPM),
    ('osc', ESC_OSC),
    ('bare_cpr', BARE_CPR),
    ('bare_da', BARE_DA),
    ('bare_da2', BARE_DA2),
    ('bare_decrpm', BARE_DECRPM),
]


def filter_terminal_responses(text: str) -> tuple[str, dict[str, int], list[str]]:
    """Filter terminal query responses from output.

    Handles both ESC-prefixed sequences and bare remnants where the
    shell has stripped the ESC byte.

    Returns:
        Tuple of (filtered_text, counts_dict, matched_strings)
    """
    counts = {}
    matched = []
    result = text

    for name, pattern in FILTER_PATTERNS:
        matches = pattern.findall(result)
        counts[name] = len(matches)
        if matches:
            matched.extend(matches)
            result = pattern.sub('', result)

    return result, counts, matched


def debug_escape_sequences(text: str) -> list[str]:
    """Find all escape sequences in text for debugging."""
    csi = re.findall(r'\x1b\[[0-9;?>]*[a-zA-Z$][a-zA-Z]?', text)
    osc = re.findall(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', text)
    bare = re.findall(r'(?<!\x1b)\[\d+;\d+[Rc]', text)
    return csi + osc + bare
