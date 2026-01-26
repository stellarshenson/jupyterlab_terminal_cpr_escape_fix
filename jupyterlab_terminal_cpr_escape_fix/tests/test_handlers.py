"""Tests for CPR escape sequence filtering."""
import pytest
from jupyterlab_terminal_cpr_escape_fix.handlers import filter_cpr_sequences


class TestFilterCprSequences:
    """Tests for the filter_cpr_sequences function."""

    def test_filters_single_cpr(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[52;1R')
        assert result == ''
        assert cpr_count == 1
        assert da_count == 0

    def test_filters_multiple_cpr(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[52;1R\x1b[13;1R\x1b[15;1R')
        assert result == ''
        assert cpr_count == 3
        assert da_count == 0

    def test_filters_cpr_mixed_with_text(self):
        result, cpr_count, da_count = filter_cpr_sequences('hello\x1b[52;1Rworld')
        assert result == 'helloworld'
        assert cpr_count == 1
        assert da_count == 0

    def test_filters_da_sequence(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[?1;2c')
        assert result == ''
        assert cpr_count == 0
        assert da_count == 1

    def test_filters_complex_da(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[?64;1;2;6;9;15;16;17;18;21;22c')
        assert result == ''
        assert cpr_count == 0
        assert da_count == 1

    def test_preserves_normal_text(self):
        result, cpr_count, da_count = filter_cpr_sequences('Hello, World!')
        assert result == 'Hello, World!'
        assert cpr_count == 0
        assert da_count == 0

    def test_preserves_color_codes(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[32mgreen\x1b[0m')
        assert result == '\x1b[32mgreen\x1b[0m'
        assert cpr_count == 0
        assert da_count == 0

    def test_preserves_cursor_movement(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[5A')
        assert result == '\x1b[5A'
        assert cpr_count == 0
        assert da_count == 0

    def test_handles_empty_string(self):
        result, cpr_count, da_count = filter_cpr_sequences('')
        assert result == ''
        assert cpr_count == 0
        assert da_count == 0

    def test_handles_multidigit_positions(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[999;999R')
        assert result == ''
        assert cpr_count == 1
        assert da_count == 0

    def test_mixed_cpr_and_da(self):
        result, cpr_count, da_count = filter_cpr_sequences('\x1b[52;1R\x1b[?1;2c\x1b[13;1R')
        assert result == ''
        assert cpr_count == 2
        assert da_count == 1
