"""Tests for terminal query response filtering."""
import pytest
from jupyterlab_terminal_cpr_escape_fix.handlers import filter_terminal_responses


class TestFilterTerminalResponses:
    """Tests for the filter_terminal_responses function."""

    def test_filters_single_cpr(self):
        result, counts = filter_terminal_responses('\x1b[52;1R')
        assert result == ''
        assert counts['cpr'] == 1

    def test_filters_multiple_cpr(self):
        result, counts = filter_terminal_responses('\x1b[52;1R\x1b[13;1R\x1b[15;1R')
        assert result == ''
        assert counts['cpr'] == 3

    def test_filters_cpr_mixed_with_text(self):
        result, counts = filter_terminal_responses('hello\x1b[52;1Rworld')
        assert result == 'helloworld'
        assert counts['cpr'] == 1

    def test_filters_da_sequence(self):
        result, counts = filter_terminal_responses('\x1b[?1;2c')
        assert result == ''
        assert counts['da'] == 1

    def test_filters_complex_da(self):
        result, counts = filter_terminal_responses('\x1b[?64;1;2;6;9;15;16;17;18;21;22c')
        assert result == ''
        assert counts['da'] == 1

    def test_filters_da2_sequence(self):
        result, counts = filter_terminal_responses('\x1b[>0;276;0c')
        assert result == ''
        assert counts['da2'] == 1

    def test_filters_decrpm_sequence(self):
        result, counts = filter_terminal_responses('\x1b[12;2$y')
        assert result == ''
        assert counts['decrpm'] == 1

    def test_filters_decrpm_with_question(self):
        result, counts = filter_terminal_responses('\x1b[?12;2$y')
        assert result == ''
        assert counts['decrpm'] == 1

    def test_filters_osc10_foreground_color(self):
        result, counts = filter_terminal_responses('\x1b]10;rgb:c3c3/c3c3/c3c3\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_filters_osc11_background_color(self):
        result, counts = filter_terminal_responses('\x1b]11;rgb:2525/2b2b/3232\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_filters_osc4_color_palette(self):
        result, counts = filter_terminal_responses('\x1b]4;1;rgb:cccc/0000/0000\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_filters_osc_with_bel_terminator(self):
        result, counts = filter_terminal_responses('\x1b]10;rgb:c3c3/c3c3/c3c3\x07')
        assert result == ''
        assert counts['osc'] == 1

    def test_preserves_normal_text(self):
        result, counts = filter_terminal_responses('Hello, World!')
        assert result == 'Hello, World!'
        assert sum(counts.values()) == 0

    def test_preserves_color_codes(self):
        result, counts = filter_terminal_responses('\x1b[32mgreen\x1b[0m')
        assert result == '\x1b[32mgreen\x1b[0m'
        assert sum(counts.values()) == 0

    def test_preserves_cursor_movement(self):
        result, counts = filter_terminal_responses('\x1b[5A')
        assert result == '\x1b[5A'
        assert sum(counts.values()) == 0

    def test_handles_empty_string(self):
        result, counts = filter_terminal_responses('')
        assert result == ''
        assert sum(counts.values()) == 0

    def test_handles_multidigit_positions(self):
        result, counts = filter_terminal_responses('\x1b[999;999R')
        assert result == ''
        assert counts['cpr'] == 1

    def test_mixed_cpr_and_da(self):
        result, counts = filter_terminal_responses('\x1b[52;1R\x1b[?1;2c\x1b[13;1R')
        assert result == ''
        assert counts['cpr'] == 2
        assert counts['da'] == 1

    def test_fish_shell_full_response(self):
        """Real fish shell response pattern seen in production."""
        text = (
            '\x1b[?1;2c'
            '\x1b[?1;2c'
            '\x1b[2;2R'
            '\x1b[3;1R'
            '\x1b[>0;276;0c'
            '\x1b]10;rgb:c3c3/c3c3/c3c3\x1b\\'
            '\x1b]11;rgb:2525/2b2b/3232\x1b\\'
            '\x1b[?12;2$y'
        )
        result, counts = filter_terminal_responses(text)
        assert result == ''
        assert counts['cpr'] == 2
        assert counts['da'] == 2
        assert counts['da2'] == 1
        assert counts['osc'] == 2
        assert counts['decrpm'] == 1
