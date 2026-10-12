"""Clear the client's terminal before a history replay (clear_before_replay).

The whole module belongs to one monkey patch; see docs/monkeypatches.md.
"""
import re

# DEC private mode set (h) or reset (l) with a parameter list such as ?1049;25h
_PRIVATE_MODE = re.compile(r'\x1b\[\?([\d;]*)([hl])')
_ALTERNATE_SCREEN_MODES = {'47', '1047', '1049'}

# Cursor home, erase screen, erase scrollback. No full reset (ESC c) and no soft
# reset (ESC [ ! p): both reset input modes (bracketed paste, mouse reporting,
# cursor keys) that must survive a plain reconnect.
_CLEAR = '\x1b[H\x1b[2J\x1b[3J'
_LEAVE_ALTERNATE = '\x1b[?1049l'
_ENTER_ALTERNATE = '\x1b[?1049h'


def _first_alternate_screen_switch(text: str) -> str | None:
    """Return 'h' or 'l' for the first alternate-screen switch in text, else None."""
    for match in _PRIVATE_MODE.finditer(text):
        if _ALTERNATE_SCREEN_MODES.intersection(match.group(1).split(';')):
            return match.group(2)
    return None


def clear_before_replay(text: str) -> str:
    """Put the sequences that empty the client's terminal in front of a replay.

    Which screen the replay starts on decides the prefix:

    - no alternate-screen switch in the replay: the screen the client shows now
      is kept, because the whole replay belongs to it
    - the first switch is an entry: the replay starts on the normal screen, so the
      prefix leaves the alternate screen first
    - the first switch is a leave: the replay starts inside the alternate screen,
      so the prefix enters it again after the clear

    Args:
        text: The buffered terminal output that TermSocket.open replays.

    Returns:
        The prefix followed by text, which is unchanged.

    Example:
        >>> clear_before_replay('$ ') == '\\x1b[H\\x1b[2J\\x1b[3J$ '
        True
    """
    switch = _first_alternate_screen_switch(text)
    if switch is None:
        return _CLEAR + text
    if switch == 'h':
        return _LEAVE_ALTERNATE + _CLEAR + text
    return _LEAVE_ALTERNATE + _CLEAR + _ENTER_ALTERNATE + text
