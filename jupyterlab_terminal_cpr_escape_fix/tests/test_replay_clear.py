"""Tests for clear_before_replay (ACC-CLEAR-58 to ACC-CLEAR-61, ACC-CLEAR-64).

This file belongs to the feature and is deleted with it; see docs/monkeypatches.md.
"""
import json
import logging
from collections import deque
from unittest import mock

import pytest

from jupyterlab_terminal_cpr_escape_fix.handlers import filter_terminal_responses
from jupyterlab_terminal_cpr_escape_fix.replay_clear import clear_before_replay

CLEAR = '\x1b[H\x1b[2J\x1b[3J'
PREFIX_NO_SWITCH = CLEAR
PREFIX_ENTRY = '\x1b[?1049l' + CLEAR
PREFIX_LEAVE = '\x1b[?1049l' + CLEAR + '\x1b[?1049h'


class TestClearBeforeReplay:
    """The pure function: which prefix goes in front of which text."""

    def test_no_switch_clears_only(self):
        text = 'line1\r\nline2\r\n\x1b[32mgreen\x1b[0m'
        assert clear_before_replay(text) == PREFIX_NO_SWITCH + text

    def test_empty_text(self):
        assert clear_before_replay('') == PREFIX_NO_SWITCH

    @pytest.mark.parametrize('mode', ['47', '1047', '1049'])
    def test_first_switch_entry(self, mode):
        text = f'history\r\n\x1b[?{mode}hfull screen'
        assert clear_before_replay(text) == PREFIX_ENTRY + text

    @pytest.mark.parametrize('mode', ['47', '1047', '1049'])
    def test_first_switch_leave(self, mode):
        text = f'screen rows\x1b[?{mode}lprompt'
        assert clear_before_replay(text) == PREFIX_LEAVE + text

    def test_parameter_list_entry(self):
        text = 'a\x1b[?1049;25hb'
        assert clear_before_replay(text) == PREFIX_ENTRY + text

    def test_parameter_list_leave(self):
        text = 'a\x1b[?25;1047lb'
        assert clear_before_replay(text) == PREFIX_LEAVE + text

    def test_only_first_switch_counts(self):
        assert clear_before_replay('\x1b[?1049h x \x1b[?1049l') == PREFIX_ENTRY + '\x1b[?1049h x \x1b[?1049l'
        assert clear_before_replay('\x1b[?1049l x \x1b[?1049h') == PREFIX_LEAVE + '\x1b[?1049l x \x1b[?1049h'

    @pytest.mark.parametrize('sequence', [
        '\x1b[?2004h',          # bracketed paste
        '\x1b[?1000h',          # mouse reporting
        '\x1b[?25l',            # cursor visibility
        '\x1b[?1048h',          # save cursor, not a screen switch
        '\x1b[?10490h',         # a different number that contains 1049
        '\x1b[1049h',           # not a private mode
        '\x1b[?1049;2004;25',   # no final byte
    ])
    def test_other_sequences_are_no_switch(self, sequence):
        assert clear_before_replay(sequence) == PREFIX_NO_SWITCH + sequence

    def test_prefix_resets_no_input_mode(self):
        """No full reset (ESC c), no soft reset (ESC [ ! p), no mode sequence
        except the alternate screen."""
        for text in ('', '\x1b[?1049hx', '\x1b[?1049lx'):
            prefix = clear_before_replay(text)[:len(clear_before_replay(text)) - len(text)]
            assert prefix in (PREFIX_NO_SWITCH, PREFIX_ENTRY, PREFIX_LEAVE)
            assert '\x1bc' not in prefix
            assert '\x1b[!p' not in prefix

    @pytest.mark.parametrize('prefix', [PREFIX_NO_SWITCH, PREFIX_ENTRY, PREFIX_LEAVE])
    def test_response_filter_leaves_prefix_intact(self, prefix):
        filtered, counts, _ = filter_terminal_responses(prefix)
        assert filtered == prefix
        assert sum(counts.values()) == 0


def _attach(chunks, live=(), spy=None, **toggles):
    """Drive the real loader over the real TermSocket.open: attach a socket
    whose terminal holds `chunks` in read_buffer, then feed `live` to it as PTY
    output. Returns the text of every stdout frame sent. `spy` is a list that
    receives 'strip' and 'clear' in call order."""
    import tornado.ioloop
    import jupyterlab_terminal_cpr_escape_fix as ext
    from jupyterlab_terminal_cpr_escape_fix import handlers, replay_clear
    from jupyter_server_terminals.handlers import TermSocket

    class FakeTerminal:
        def __init__(self):
            self.clients = []
            self.read_buffer = deque(chunks, maxlen=1000)
            self.ptyproc = None

    class FakeTermManager:
        def get_terminal(self, name):
            return FakeTerminal()

    class FakeLoop:
        def call_later(self, delay, fn, *args):
            pass

    class Sock(TermSocket):
        """Real TermSocket methods; no tornado request, frames captured."""
        ping_interval = 0
        request = mock.MagicMock(path='/terminals/websocket/8')

        def __init__(self):
            self.term_manager = FakeTermManager()
            self._logger = logging.getLogger(__name__)
            self._enable_output_logging = False
            self.frames = []

        def write_message(self, message, binary=False):
            self.frames.append(json.loads(message))

    def recording(name, function):
        def call(text):
            spy.append(name)
            return function(text)
        return call

    patches = [mock.patch.dict(ext.DEFAULTS, toggles),
               mock.patch.object(tornado.ioloop.IOLoop, 'current', return_value=FakeLoop())]
    if spy is not None:
        patches.append(mock.patch.object(
            handlers, 'strip_replay_queries', recording('strip', handlers.strip_replay_queries)))
        patches.append(mock.patch.object(
            replay_clear, 'clear_before_replay', recording('clear', replay_clear.clear_before_replay)))
    orig_open = TermSocket.open
    orig_read = TermSocket.on_pty_read
    try:
        for patch in patches:
            patch.start()
        ext._load_jupyter_server_extension(mock.MagicMock())
        sock = Sock()
        TermSocket.open(sock, '8')
        for text in live:
            sock.on_pty_read(text)
    finally:
        for patch in reversed(patches):
            patch.stop()
        TermSocket.open = orig_open
        TermSocket.on_pty_read = orig_read
    return [text for kind, text in sock.frames if kind == 'stdout']


class TestPatchedOpen:
    """The prefix in front of the replay that TermSocket.open sends."""

    def test_default_is_on(self):
        import jupyterlab_terminal_cpr_escape_fix as ext

        assert ext.DEFAULTS['clear_before_replay'] is True

    def test_prefix_present_replay_bytes_unchanged(self):
        assert _attach(['a', 'b\r\n', '$ ']) == [PREFIX_NO_SWITCH + 'ab\r\n$ ']

    def test_alternate_screen_branches_in_open(self):
        assert _attach(['x\x1b[?1049h', 'y']) == [PREFIX_ENTRY + 'x\x1b[?1049hy']
        assert _attach(['x\x1b[?1049l', 'y']) == [PREFIX_LEAVE + 'x\x1b[?1049ly']

    def test_prefix_survives_response_filter_with_replies_in_replay(self):
        frames = _attach(['a\x1b[2;2R', 'b'])
        assert frames == [PREFIX_NO_SWITCH + 'ab']

    def test_switch_off_replay_is_unchanged(self):
        assert _attach(['a', 'b'], clear_before_replay=False) == ['ab']

    def test_live_output_gets_no_prefix(self):
        assert _attach(['old'], live=['live 1', 'live 2']) == [PREFIX_NO_SWITCH + 'old', 'live 1', 'live 2']

    def test_nothing_sent_under_suppress_buffer_replay(self):
        assert _attach(['a', 'b'], suppress_buffer_replay=True) == []
        assert _attach(['a'], live=['live'], suppress_buffer_replay=True) == ['live']

    def test_clear_runs_with_query_stripping_off(self):
        assert _attach(['a\x1b[cb', '$ '], strip_replay_queries=False) == [PREFIX_NO_SWITCH + 'a\x1b[cb$ ']
        # the replay hook is removed after open: live output is unchanged
        assert _attach(['a'], live=['live'], strip_replay_queries=False) == [PREFIX_NO_SWITCH + 'a', 'live']

    def test_clear_runs_with_repaint_off(self):
        assert _attach(['a'], repaint_on_attach=False) == [PREFIX_NO_SWITCH + 'a']

    def test_clear_is_the_only_installed_step(self):
        assert _attach(['a'], strip_replay_queries=False, repaint_on_attach=False) == [PREFIX_NO_SWITCH + 'a']

    def test_empty_buffer_still_clears(self):
        """terminado replays only a non-empty buffer; the clear is sent anyway."""
        assert _attach([], live=['banner']) == [PREFIX_NO_SWITCH, 'banner']

    def test_empty_buffer_switch_off_sends_nothing(self):
        assert _attach([], live=['banner'], clear_before_replay=False) == ['banner']

    def test_empty_buffer_under_suppress_buffer_replay_sends_nothing(self):
        assert _attach([], suppress_buffer_replay=True) == []
        assert _attach([], live=['banner'], suppress_buffer_replay=True) == ['banner']

    def test_all_replay_steps_off_sends_replay_unchanged(self):
        assert _attach(
            ['a\x1b[cb', '$ '], clear_before_replay=False, strip_replay_queries=False,
        ) == ['a\x1b[cb$ ']

    def test_order_strip_then_clear(self):
        spy = []
        frames = _attach(['a\x1b[cb', '$ '], spy=spy)
        assert spy == ['strip', 'clear']
        assert frames == [PREFIX_NO_SWITCH + 'ab$ ']

    def test_spy_sees_only_enabled_steps(self):
        spy = []
        _attach(['a'], spy=spy, strip_replay_queries=False)
        assert spy == ['clear']
        spy = []
        _attach(['a'], spy=spy, clear_before_replay=False)
        assert spy == ['strip']
