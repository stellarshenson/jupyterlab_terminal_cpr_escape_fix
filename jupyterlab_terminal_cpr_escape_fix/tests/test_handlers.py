"""Tests for terminal query response filtering."""
import pytest
from jupyterlab_terminal_cpr_escape_fix.handlers import filter_terminal_responses


class TestFilterEscPrefixed:
    """Tests for ESC-prefixed escape sequences."""

    def test_filters_cpr(self):
        result, counts = filter_terminal_responses('\x1b[52;1R')
        assert result == ''
        assert counts['cpr'] == 1

    def test_filters_da(self):
        result, counts = filter_terminal_responses('\x1b[?1;2c')
        assert result == ''
        assert counts['da'] == 1

    def test_filters_da2(self):
        result, counts = filter_terminal_responses('\x1b[>0;276;0c')
        assert result == ''
        assert counts['da2'] == 1

    def test_filters_decrpm(self):
        result, counts = filter_terminal_responses('\x1b[?12;2$y')
        assert result == ''
        assert counts['decrpm'] == 1

    def test_filters_osc10(self):
        result, counts = filter_terminal_responses('\x1b]10;rgb:c3c3/c3c3/c3c3\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_filters_osc11(self):
        result, counts = filter_terminal_responses('\x1b]11;rgb:2525/2b2b/3232\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_preserves_color_codes(self):
        result, counts = filter_terminal_responses('\x1b[32mgreen\x1b[0m')
        assert result == '\x1b[32mgreen\x1b[0m'
        assert sum(counts.values()) == 0

    def test_preserves_cursor_movement(self):
        result, counts = filter_terminal_responses('\x1b[5A')
        assert result == '\x1b[5A'
        assert sum(counts.values()) == 0


class TestFilterBareSequences:
    """Tests for bare sequences (ESC stripped by shell)."""

    def test_filters_bare_cpr(self):
        """Fish shell strips ESC, outputs [row;colR as bare text."""
        result, counts = filter_terminal_responses('[2;1R')
        assert result == ''
        assert counts['bare_cpr'] == 1

    def test_filters_multiple_bare_cpr(self):
        result, counts = filter_terminal_responses('[2;2R[3;1R')
        assert result == ''
        assert counts['bare_cpr'] == 2

    def test_filters_bare_da(self):
        result, counts = filter_terminal_responses('[?1;2c')
        assert result == ''
        assert counts['bare_da'] == 1

    def test_filters_bare_da2(self):
        result, counts = filter_terminal_responses('[>0;276;0c')
        assert result == ''
        assert counts['bare_da2'] == 1

    def test_filters_bare_decrpm(self):
        result, counts = filter_terminal_responses('[?12;2$y')
        assert result == ''
        assert counts['bare_decrpm'] == 1

    def test_bare_cpr_mixed_with_text(self):
        result, counts = filter_terminal_responses('prompt$ [2;2R[3;1R ')
        assert result == 'prompt$  '
        assert counts['bare_cpr'] == 2

    def test_bare_cpr_in_fish_prompt(self):
        """Real fish shell output: bare CPR at end of prompt line."""
        result, counts = filter_terminal_responses(' base  ~/workspace  [2;2R[3;1R ')
        assert result == ' base  ~/workspace   '
        assert counts['bare_cpr'] == 2


class TestFilterMixed:
    """Tests for mixed ESC-prefixed and bare sequences."""

    def test_fish_shell_full_response(self):
        """Real fish shell response with all sequence types."""
        text = (
            '\x1b[?1;2c'
            '\x1b[2;2R'
            '\x1b[>0;276;0c'
            '\x1b]10;rgb:c3c3/c3c3/c3c3\x1b\\'
            '\x1b]11;rgb:2525/2b2b/3232\x1b\\'
            '\x1b[?12;2$y'
        )
        result, counts = filter_terminal_responses(text)
        assert result == ''

    def test_mixed_esc_and_bare(self):
        text = '\x1b[52;1R[2;2R[3;1R'
        result, counts = filter_terminal_responses(text)
        assert result == ''
        assert counts['cpr'] == 1
        assert counts['bare_cpr'] == 2

    def test_preserves_normal_text(self):
        result, counts = filter_terminal_responses('Hello, World!')
        assert result == 'Hello, World!'
        assert sum(counts.values()) == 0

    def test_handles_empty_string(self):
        result, counts = filter_terminal_responses('')
        assert result == ''
        assert sum(counts.values()) == 0

    def test_preserves_normal_brackets(self):
        """Normal text with brackets should not be filtered."""
        result, counts = filter_terminal_responses('array[0] = 5')
        assert result == 'array[0] = 5'
        assert sum(counts.values()) == 0

    def test_fish_pty_actual_output(self):
        """Actual PTY output observed from fish shell CPR handling.

        Fish receives ESC[5;1R, strips ESC, outputs bare [5;1R
        interspersed with cursor movement sequences.
        """
        # Simplified version of actual fish output
        text = '[5;\r\x1b[71C1R\r\x1b[73C\x08\x08\x08\x08\x08[5;1R\r\x1b[73C'
        result, counts = filter_terminal_responses(text)
        # The bare [5;1R should be filtered
        assert '[5;1R' not in result
        assert counts['bare_cpr'] >= 1
