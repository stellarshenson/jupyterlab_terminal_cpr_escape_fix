"""Tests for terminal query response filtering."""
import pytest
from jupyterlab_terminal_cpr_escape_fix.handlers import filter_terminal_responses


class TestFilterEscPrefixed:
    """Tests for ESC-prefixed escape sequences."""

    def test_filters_cpr(self):
        result, counts, _ = filter_terminal_responses('\x1b[52;1R')
        assert result == ''
        assert counts['cpr'] == 1

    def test_filters_da(self):
        result, counts, _ = filter_terminal_responses('\x1b[?1;2c')
        assert result == ''
        assert counts['da'] == 1

    def test_filters_da2(self):
        result, counts, _ = filter_terminal_responses('\x1b[>0;276;0c')
        assert result == ''
        assert counts['da2'] == 1

    def test_filters_decrpm(self):
        result, counts, _ = filter_terminal_responses('\x1b[?12;2$y')
        assert result == ''
        assert counts['decrpm'] == 1

    def test_filters_osc10(self):
        result, counts, _ = filter_terminal_responses('\x1b]10;rgb:c3c3/c3c3/c3c3\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_filters_osc11(self):
        result, counts, _ = filter_terminal_responses('\x1b]11;rgb:2525/2b2b/3232\x1b\\')
        assert result == ''
        assert counts['osc'] == 1

    def test_preserves_osc52_clipboard_bel(self):
        """OSC 52 clipboard sequences must pass through for clipboard extension."""
        osc52 = '\x1b]52;c;SGVsbG8gV29ybGQ=\x07'
        result, counts, _ = filter_terminal_responses(osc52)
        assert result == osc52
        assert counts['osc'] == 0

    def test_preserves_osc52_clipboard_st(self):
        """OSC 52 with ST terminator must also pass through."""
        osc52 = '\x1b]52;c;SGVsbG8gV29ybGQ=\x1b\\'
        result, counts, _ = filter_terminal_responses(osc52)
        assert result == osc52
        assert counts['osc'] == 0

    def test_filters_osc_but_preserves_osc52(self):
        """Other OSC filtered, OSC 52 preserved in same text."""
        osc10 = '\x1b]10;rgb:c3c3/c3c3/c3c3\x1b\\'
        osc52 = '\x1b]52;c;SGVsbG8=\x07'
        result, counts, _ = filter_terminal_responses(osc10 + osc52)
        assert result == osc52
        assert counts['osc'] == 1

    def test_preserves_color_codes(self):
        result, counts, _ = filter_terminal_responses('\x1b[32mgreen\x1b[0m')
        assert result == '\x1b[32mgreen\x1b[0m'
        assert sum(counts.values()) == 0

    def test_preserves_cursor_movement(self):
        result, counts, _ = filter_terminal_responses('\x1b[5A')
        assert result == '\x1b[5A'
        assert sum(counts.values()) == 0


class TestFilterBareSequences:
    """Tests for bare sequences (ESC stripped by shell)."""

    def test_filters_bare_cpr(self):
        """Fish shell strips ESC, outputs [row;colR as bare text."""
        result, counts, _ = filter_terminal_responses('[2;1R')
        assert result == ''
        assert counts['bare_cpr'] == 1

    def test_filters_multiple_bare_cpr(self):
        result, counts, _ = filter_terminal_responses('[2;2R[3;1R')
        assert result == ''
        assert counts['bare_cpr'] == 2

    def test_filters_bare_da(self):
        result, counts, _ = filter_terminal_responses('[?1;2c')
        assert result == ''
        assert counts['bare_da'] == 1

    def test_filters_bare_da2(self):
        result, counts, _ = filter_terminal_responses('[>0;276;0c')
        assert result == ''
        assert counts['bare_da2'] == 1

    def test_filters_bare_decrpm(self):
        result, counts, _ = filter_terminal_responses('[?12;2$y')
        assert result == ''
        assert counts['bare_decrpm'] == 1

    def test_bare_cpr_mixed_with_text(self):
        result, counts, _ = filter_terminal_responses('prompt$ [2;2R[3;1R ')
        assert result == 'prompt$  '
        assert counts['bare_cpr'] == 2

    def test_bare_cpr_in_fish_prompt(self):
        """Real fish shell output: bare CPR at end of prompt line."""
        result, counts, _ = filter_terminal_responses(' base  ~/workspace  [2;2R[3;1R ')
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
        result, counts, _ = filter_terminal_responses(text)
        assert result == ''

    def test_mixed_esc_and_bare(self):
        text = '\x1b[52;1R[2;2R[3;1R'
        result, counts, _ = filter_terminal_responses(text)
        assert result == ''
        assert counts['cpr'] == 1
        assert counts['bare_cpr'] == 2

    def test_preserves_normal_text(self):
        result, counts, _ = filter_terminal_responses('Hello, World!')
        assert result == 'Hello, World!'
        assert sum(counts.values()) == 0

    def test_handles_empty_string(self):
        result, counts, _ = filter_terminal_responses('')
        assert result == ''
        assert sum(counts.values()) == 0

    def test_preserves_normal_brackets(self):
        """Normal text with brackets should not be filtered."""
        result, counts, _ = filter_terminal_responses('array[0] = 5')
        assert result == 'array[0] = 5'
        assert sum(counts.values()) == 0

    def test_fish_pty_actual_output(self):
        """Actual PTY output observed from fish shell CPR handling.

        Fish receives ESC[5;1R, strips ESC, outputs bare [5;1R
        interspersed with cursor movement sequences.
        """
        # Simplified version of actual fish output
        text = '[5;\r\x1b[71C1R\r\x1b[73C\x08\x08\x08\x08\x08[5;1R\r\x1b[73C'
        result, counts, _ = filter_terminal_responses(text)
        # The bare [5;1R should be filtered
        assert '[5;1R' not in result
        assert counts['bare_cpr'] >= 1


class TestSequenceComplement:
    """Complement tests: sequences that must NOT be filtered."""

    # --- Normal terminal output sequences (must be preserved) ---

    def test_preserves_sgr_color_256(self):
        """256-color SGR: ESC[38;5;NNNm"""
        text = '\x1b[38;5;231m'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_sgr_color_rgb(self):
        """RGB color SGR: ESC[38;2;R;G;Bm"""
        text = '\x1b[38;2;255;128;0m'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_sgr_reset(self):
        text = '\x1b[0m'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_cursor_up(self):
        text = '\x1b[5A'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_cursor_down(self):
        text = '\x1b[3B'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_cursor_forward(self):
        text = '\x1b[71C'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_cursor_back(self):
        text = '\x1b[2D'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_cursor_position(self):
        """CUP: ESC[row;colH - cursor positioning (not a response)."""
        text = '\x1b[10;20H'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_erase_line(self):
        text = '\x1b[K'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_erase_display(self):
        text = '\x1b[2J'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_scroll_up(self):
        text = '\x1b[3S'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_bracketed_paste_mode(self):
        """ESC[?2004h/l - bracketed paste mode on/off."""
        text = '\x1b[?2004h'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_alternate_screen(self):
        """ESC[?1049h/l - alternate screen buffer."""
        text = '\x1b[?1049h'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_dec_private_mode_set(self):
        """ESC[?25h - show cursor."""
        text = '\x1b[?25h'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_window_title_osc0(self):
        """OSC 0 sets window title - must NOT be filtered."""
        text = '\x1b]0;My Terminal\x07'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text
        assert counts['osc'] == 0

    def test_preserves_osc7_cwd(self):
        """OSC 7 sets working directory - must NOT be filtered."""
        text = '\x1b]7;file:///home/user\x07'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_osc8_hyperlink(self):
        """OSC 8 hyperlinks - must NOT be filtered."""
        text = '\x1b]8;;https://example.com\x07link\x1b]8;;\x07'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_osc133_prompt_mark(self):
        """OSC 133 shell integration - must NOT be filtered."""
        text = '\x1b]133;A\x07'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_osc10_query(self):
        """OSC 10 foreground color QUERY (?) - must pass through to terminal."""
        text = '\x1b]10;?\x07'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_osc11_query(self):
        """OSC 11 background color QUERY (?) - must pass through to terminal."""
        text = '\x1b]11;?\x07'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_osc12_query(self):
        """OSC 12 cursor color QUERY (?) - must pass through to terminal."""
        text = '\x1b]12;?\x1b\\'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_da2_query(self):
        """DA2 QUERY (ESC[>c or ESC[>0c) - must pass through to terminal."""
        assert filter_terminal_responses('\x1b[>c')[0] == '\x1b[>c'
        assert filter_terminal_responses('\x1b[>0c')[0] == '\x1b[>0c'

    def test_preserves_da_query(self):
        """DA QUERY (ESC[c or ESC[?c) - must pass through to terminal."""
        # Note: ESC[c has no ? prefix so our regex doesn't match it anyway
        # ESC[?c alone is also a query form
        assert filter_terminal_responses('\x1b[c')[0] == '\x1b[c'
        assert filter_terminal_responses('\x1b[?c')[0] == '\x1b[?c'

    def test_preserves_osc52_empty_payload(self):
        """OSC 52 with empty payload (clipboard query)."""
        osc52 = '\x1b]52;c;\x07'
        result, counts, _ = filter_terminal_responses(osc52)
        assert result == osc52
        assert counts['osc'] == 0

    def test_preserves_osc52_primary_selection(self):
        """OSC 52 with primary selection target."""
        osc52 = '\x1b]52;p;dGVzdA==\x07'
        result, counts, _ = filter_terminal_responses(osc52)
        assert result == osc52

    def test_preserves_osc52_large_payload(self):
        """OSC 52 with large base64 payload."""
        import base64
        payload = base64.b64encode(b'A' * 1000).decode()
        osc52 = f'\x1b]52;c;{payload}\x07'
        result, counts, _ = filter_terminal_responses(osc52)
        assert result == osc52

    # --- Plain text that resembles sequences (must be preserved) ---

    def test_preserves_array_index(self):
        text = 'data[0] = value'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_matrix_notation(self):
        text = 'matrix[3][5]'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_markdown_link(self):
        text = '[link](https://example.com)'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_git_output(self):
        text = '[main 6b3772e] fix: some commit message'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    def test_preserves_json_brackets(self):
        text = '{"items": [1, 2, 3]}'
        result, counts, _ = filter_terminal_responses(text)
        assert result == text

    # --- Matched strings return value ---

    def test_matched_strings_returned(self):
        text = '\x1b[2;1R\x1b[?1;2c'
        _, _, matched = filter_terminal_responses(text)
        assert '\x1b[2;1R' in matched
        assert '\x1b[?1;2c' in matched

    def test_matched_strings_include_bare(self):
        text = '[2;2R[3;1R'
        _, _, matched = filter_terminal_responses(text)
        assert '[2;2R' in matched
        assert '[3;1R' in matched

    def test_matched_strings_empty_when_nothing_filtered(self):
        _, _, matched = filter_terminal_responses('hello world')
        assert matched == []
