"""Filtered terminal websocket handler.

Filters terminal query responses that appear as literal text when
reconnecting to idle terminals. Fish shell (and others) strip the ESC
byte from responses and echo the remainder as bare text, so we filter
both ESC-prefixed and bare patterns.
"""
import logging
import re

# Patterns WITH ESC prefix (terminal RESPONSE sequences)
# Only match responses - not queries. Queries are written by shells asking
# the terminal for info; stripping them breaks terminal capability negotiation.
# CPR response: ESC[row;colR (requires two numeric params)
# DA response:  ESC[?p1;p2;...c (requires params after ?)
# DA2 response: ESC[>p1;p2;p3c (requires semicolon-separated params; bare ESC[>c is a query)
# DECRPM:       ESC[?mode;value$y
# OSC:          every ESC]N;... and ESC]4;n;... payload (N = 10, 11, 12) not starting
#               with ?, so colour set commands (ESC]11;#282828 BEL, ESC]4;1;rgb:..ST)
#               are removed as well as responses; queries ESC]N;? and ESC]4;n;? are kept
ESC_CPR = re.compile(r'\x1b\[\d+;\d+R')
ESC_DA = re.compile(r'\x1b\[\?\d+[\d;]*c')
ESC_DA2 = re.compile(r'\x1b\[>\d+;\d+[\d;]*c')
ESC_DECRPM = re.compile(r'\x1b\[\??\d+;\d+\$y')
ESC_OSC = re.compile(r'\x1b\](?:4;\d+|10|11|12);(?!\?)[^\x07\x1b]*(?:\x07|\x1b\\)')

# Patterns WITHOUT ESC prefix (bare remnants after shell strips ESC)
# Fish shell receives ESC[row;colR, strips ESC, outputs [row;colR
# These use negative lookbehind to avoid matching ESC-prefixed sequences twice
BARE_CPR = re.compile(r'(?<!\x1b)\[\d+;\d+R')
BARE_DA = re.compile(r'(?<!\x1b)\[\?\d+[\d;]*c')
BARE_DA2 = re.compile(r'(?<!\x1b)\[>\d+;\d+[\d;]*c')
BARE_DECRPM = re.compile(r'(?<!\x1b)\[\??\d+;\d+\$y')
# Bare OSC color response: fish strips ESC from BOTH the ] introducer and the
# ST terminator, so ESC]11;rgb:..ST becomes ]11;rgb:..\ as literal text.
# rgb:-anchored to keep the false-positive surface near zero. Toggled via
# DEFAULTS['filter_osc_color_responses'] in __init__ (default on).
BARE_OSC = re.compile(r'(?<!\x1b)\](?:4|10|11|12);(?:\d+;)?rgb:[0-9a-fA-F/]+(?:\x07|\\)')

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
    ('bare_osc', BARE_OSC),
]

# Terminal QUERY sequences that xterm.js answers. Applied only to the buffer
# replay of TermSocket.open (strip_replay_queries), never to live output: the
# client parses the replay as live output and answers every query in it, and
# the shell reads those answers as typed text.
# OSC color:  ESC]4;n;?  ESC]10;?  ESC]11;?  ESC]12;?  (BEL or ST), and the
#             chained forms ESC]4;n;?;m;?  ESC]10;?;?
# DA / DA2:   ESC[c  ESC[0c  ESC[>c  ESC[>0c
# DSR / CPR:  ESC[5n  ESC[6n  ESC[?6n
# DECRQM:     ESC[?mode$p  ESC[mode$p
# DECRQSS:    ESC P $q text ST
REPLAY_QUERY = re.compile(
    r'\x1b\](?:4(?:;\d+;\?)+|(?:10|11|12)(?:;\?)+)(?:\x07|\x1b\\)'
    r'|\x1b\[>?0?c'
    r'|\x1b\[(?:5|6|\?6)n'
    r'|\x1b\[\??\d+\$p'
    r'|\x1bP\$q[^\x1b]*\x1b\\'
)


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


def strip_replay_queries(text: str) -> str:
    """Remove terminal queries from a buffer replay.

    A run of queries that ends the text is kept: nothing was printed after
    it, so the program that sent it may still be waiting for the answer.
    """
    keep_from = len(text)
    for match in reversed(list(REPLAY_QUERY.finditer(text))):
        if match.end() != keep_from:
            break
        keep_from = match.start()
    return REPLAY_QUERY.sub('', text[:keep_from]) + text[keep_from:]


def debug_escape_sequences(text: str) -> list[str]:
    """Find all escape sequences in text for debugging."""
    csi = re.findall(r'\x1b\[[0-9;?>]*[a-zA-Z$][a-zA-Z]?', text)
    osc = re.findall(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', text)
    bare = re.findall(r'(?<!\x1b)\[\d+;\d+[Rc]', text)
    return csi + osc + bare
