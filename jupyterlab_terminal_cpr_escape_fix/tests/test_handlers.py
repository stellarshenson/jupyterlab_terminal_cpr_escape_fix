"""Tests for CPR escape sequence filtering."""
import pytest
from jupyterlab_terminal_cpr_escape_fix.handlers import filter_cpr_sequences


class TestFilterCprSequences:
    """Tests for the filter_cpr_sequences function."""

    def test_filters_single_cpr(self):
        result, counts = filter_cpr_sequences('\x1b[52;1R')
        assert result == ''
        assert counts['cpr'] == 1
        assert counts['da'] == 0
        assert counts['decrpm'] == 0

    def test_filters_multiple_cpr(self):
        result, counts = filter_cpr_sequences('\x1b[52;1R\x1b[13;1R\x1b[15;1R')
        assert result == ''
        assert counts['cpr'] == 3

    def test_filters_cpr_mixed_with_text(self):
        result, counts = filter_cpr_sequences('hello\x1b[52;1Rworld')
        assert result == 'helloworld'
        assert counts['cpr'] == 1

    def test_filters_da_sequence(self):
        result, counts = filter_cpr_sequences('\x1b[?1;2c')
        assert result == ''
        assert counts['da'] == 1

    def test_filters_complex_da(self):
        result, counts = filter_cpr_sequences('\x1b[?64;1;2;6;9;15;16;17;18;21;22c')
        assert result == ''
        assert counts['da'] == 1

    def test_filters_da2_sequence(self):
        result, counts = filter_cpr_sequences('\x1b[>1;2;3c')
        assert result == ''
        assert counts['da2'] == 1

    def test_filters_decrpm_sequence(self):
        result, counts = filter_cpr_sequences('\x1b[12;2$y')
        assert result == ''
        assert counts['decrpm'] == 1

    def test_filters_decrpm_with_question(self):
        result, counts = filter_cpr_sequences('\x1b[?12;2$y')
        assert result == ''
        assert counts['decrpm'] == 1

    def test_preserves_normal_text(self):
        result, counts = filter_cpr_sequences('Hello, World!')
        assert result == 'Hello, World!'
        assert sum(counts.values()) == 0

    def test_preserves_color_codes(self):
        result, counts = filter_cpr_sequences('\x1b[32mgreen\x1b[0m')
        assert result == '\x1b[32mgreen\x1b[0m'
        assert sum(counts.values()) == 0

    def test_preserves_cursor_movement(self):
        result, counts = filter_cpr_sequences('\x1b[5A')
        assert result == '\x1b[5A'
        assert sum(counts.values()) == 0

    def test_handles_empty_string(self):
        result, counts = filter_cpr_sequences('')
        assert result == ''
        assert sum(counts.values()) == 0

    def test_handles_multidigit_positions(self):
        result, counts = filter_cpr_sequences('\x1b[999;999R')
        assert result == ''
        assert counts['cpr'] == 1

    def test_mixed_cpr_and_da(self):
        result, counts = filter_cpr_sequences('\x1b[52;1R\x1b[?1;2c\x1b[13;1R')
        assert result == ''
        assert counts['cpr'] == 2
        assert counts['da'] == 1

    def test_mixed_all_types(self):
        result, counts = filter_cpr_sequences('\x1b[52;1R\x1b[?1;2c\x1b[>1;2c\x1b[12;2$y')
        assert result == ''
        assert counts['cpr'] == 1
        assert counts['da'] == 1
        assert counts['da2'] == 1
        assert counts['decrpm'] == 1

    def test_fish_shell_response_pattern(self):
        # Pattern seen from fish shell: 2RR0;276;0c12;2$y
        # This is actually multiple sequences concatenated without ESC
        # The real sequences would be: ESC[2;1R ESC[?0;276;0c ESC[12;2$y
        text = '\x1b[2;1R\x1b[?0;276;0c\x1b[12;2$y'
        result, counts = filter_cpr_sequences(text)
        assert result == ''
        assert counts['cpr'] == 1
        assert counts['da'] == 1
        assert counts['decrpm'] == 1
