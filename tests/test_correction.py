"""Tests for the correction engine.

Phase 4 tests for:
- Casing detection (lowercase, Capitalized, UPPERCASE, mixed)
- Casing application/preservation
- Keyboard simulation
- CorrectionEngine class
"""

import pytest
from unittest.mock import patch, MagicMock, call

from custom_autocorrect.correction import (
    detect_casing_pattern,
    apply_casing,
    perform_correction,
    CorrectionEngine,
)


# =============================================================================
# Tests for detect_casing_pattern()
# =============================================================================


class TestDetectCasingPattern:
    """Tests for casing pattern detection."""

    def test_lowercase_simple(self):
        """Simple lowercase words are detected."""
        assert detect_casing_pattern("teh") == "lowercase"
        assert detect_casing_pattern("hello") == "lowercase"
        assert detect_casing_pattern("world") == "lowercase"

    def test_lowercase_with_numbers(self):
        """Lowercase with numbers is still lowercase."""
        assert detect_casing_pattern("hello123") == "lowercase"
        assert detect_casing_pattern("test1") == "lowercase"

    def test_uppercase_simple(self):
        """Simple uppercase words are detected."""
        assert detect_casing_pattern("TEH") == "uppercase"
        assert detect_casing_pattern("HELLO") == "uppercase"
        assert detect_casing_pattern("WORLD") == "uppercase"

    def test_uppercase_with_numbers(self):
        """Uppercase with numbers is still uppercase."""
        assert detect_casing_pattern("HELLO123") == "uppercase"
        assert detect_casing_pattern("TEST1") == "uppercase"

    def test_capitalized_simple(self):
        """Capitalized words are detected."""
        assert detect_casing_pattern("Teh") == "capitalized"
        assert detect_casing_pattern("Hello") == "capitalized"
        assert detect_casing_pattern("World") == "capitalized"

    def test_capitalized_with_numbers(self):
        """Capitalized with numbers is still capitalized."""
        assert detect_casing_pattern("Hello123") == "capitalized"
        assert detect_casing_pattern("Test1") == "capitalized"

    def test_mixed_simple(self):
        """Mixed case words are detected."""
        assert detect_casing_pattern("tEh") == "mixed"
        assert detect_casing_pattern("hElLo") == "mixed"
        assert detect_casing_pattern("HeLLo") == "mixed"
        assert detect_casing_pattern("tEsT") == "mixed"

    def test_mixed_camel_case(self):
        """CamelCase is detected as mixed."""
        assert detect_casing_pattern("camelCase") == "mixed"
        assert detect_casing_pattern("iPhone") == "mixed"

    def test_mixed_all_caps_prefix(self):
        """Words starting with multiple caps are mixed."""
        assert detect_casing_pattern("HTMLParser") == "mixed"
        assert detect_casing_pattern("XMLFile") == "mixed"

    def test_single_character_lowercase(self):
        """Single lowercase character is lowercase."""
        assert detect_casing_pattern("a") == "lowercase"
        assert detect_casing_pattern("x") == "lowercase"

    def test_single_character_uppercase(self):
        """Single uppercase character is uppercase."""
        assert detect_casing_pattern("A") == "uppercase"
        assert detect_casing_pattern("X") == "uppercase"

    def test_empty_string(self):
        """Empty string returns lowercase (safe default)."""
        assert detect_casing_pattern("") == "lowercase"

    def test_numbers_only(self):
        """Numbers only returns lowercase (safe default)."""
        assert detect_casing_pattern("123") == "lowercase"
        assert detect_casing_pattern("42") == "lowercase"

    def test_unicode_lowercase(self):
        """Unicode lowercase letters are handled."""
        assert detect_casing_pattern("café") == "lowercase"

    def test_unicode_uppercase(self):
        """Unicode uppercase letters are handled."""
        assert detect_casing_pattern("CAFÉ") == "uppercase"

    def test_unicode_capitalized(self):
        """Unicode capitalized words are handled."""
        assert detect_casing_pattern("Café") == "capitalized"


# =============================================================================
# Tests for apply_casing()
# =============================================================================


class TestApplyCasing:
    """Tests for applying casing patterns to corrections."""

    def test_lowercase_to_lowercase(self):
        """Lowercase original produces lowercase correction."""
        assert apply_casing("teh", "the") == "the"
        assert apply_casing("adn", "and") == "and"
        assert apply_casing("hte", "the") == "the"

    def test_lowercase_with_uppercase_correction(self):
        """Lowercase original lowercases even uppercase corrections."""
        assert apply_casing("teh", "THE") == "the"
        assert apply_casing("adn", "AND") == "and"

    def test_uppercase_to_uppercase(self):
        """Uppercase original produces uppercase correction."""
        assert apply_casing("TEH", "the") == "THE"
        assert apply_casing("ADN", "and") == "AND"
        assert apply_casing("HTE", "the") == "THE"

    def test_uppercase_with_lowercase_correction(self):
        """Uppercase original uppercases even lowercase corrections."""
        assert apply_casing("TEH", "the") == "THE"

    def test_capitalized_to_capitalized(self):
        """Capitalized original produces capitalized correction."""
        assert apply_casing("Teh", "the") == "The"
        assert apply_casing("Adn", "and") == "And"
        assert apply_casing("Hte", "the") == "The"

    def test_capitalized_with_uppercase_correction(self):
        """Capitalized original capitalizes even uppercase corrections."""
        assert apply_casing("Teh", "THE") == "The"

    def test_mixed_falls_back_to_correction(self):
        """Mixed case uses correction as-is (safe fallback)."""
        assert apply_casing("tEh", "the") == "the"
        assert apply_casing("hElLo", "hello") == "hello"
        assert apply_casing("TEh", "the") == "the"

    def test_mixed_preserves_correction_case(self):
        """Mixed case preserves whatever case the correction has."""
        assert apply_casing("tEh", "THE") == "THE"
        assert apply_casing("hElLo", "Hello") == "Hello"

    def test_different_lengths(self):
        """Corrections can be different length than original."""
        assert apply_casing("tht", "that") == "that"
        assert apply_casing("THT", "that") == "THAT"
        assert apply_casing("Tht", "that") == "That"

    def test_longer_to_shorter(self):
        """Longer typo to shorter correction works."""
        assert apply_casing("becuase", "because") == "because"
        assert apply_casing("BECUASE", "because") == "BECAUSE"

    def test_empty_original(self):
        """Empty original returns correction as-is."""
        assert apply_casing("", "the") == "the"

    def test_empty_correction(self):
        """Empty correction returns empty."""
        assert apply_casing("teh", "") == ""

    def test_both_empty(self):
        """Both empty returns empty."""
        assert apply_casing("", "") == ""

    def test_unicode_preserved(self):
        """Unicode characters in correction are preserved."""
        assert apply_casing("cafe", "café") == "café"
        assert apply_casing("CAFE", "café") == "CAFÉ"


# =============================================================================
# Tests for perform_correction()
# =============================================================================


class TestPerformCorrection:
    """Tests for keyboard simulation."""

    @patch("custom_autocorrect.correction.keyboard")
    def test_sends_correct_backspace_count(self, mock_keyboard):
        """Should send typo_length + 1 backspaces."""
        perform_correction(3, "the")

        # 3 (typo) + 1 (space) = 4 backspaces
        backspace_calls = [
            c for c in mock_keyboard.press_and_release.call_args_list
            if c == call("backspace")
        ]
        assert len(backspace_calls) == 4

    @patch("custom_autocorrect.correction.keyboard")
    def test_sends_correct_backspace_for_longer_word(self, mock_keyboard):
        """Should send correct backspaces for longer words."""
        perform_correction(7, "because")

        # 7 (typo) + 1 (space) = 8 backspaces
        backspace_calls = [
            c for c in mock_keyboard.press_and_release.call_args_list
            if c == call("backspace")
        ]
        assert len(backspace_calls) == 8

    @patch("custom_autocorrect.correction.keyboard")
    def test_types_correction_with_space(self, mock_keyboard):
        """Should type correction followed by space."""
        perform_correction(3, "the")

        mock_keyboard.write.assert_called_once_with("the ")

    @patch("custom_autocorrect.correction.keyboard")
    def test_returns_true_on_success(self, mock_keyboard):
        """Should return True when successful."""
        result = perform_correction(3, "the")
        assert result is True

    @patch("custom_autocorrect.correction.keyboard")
    def test_returns_false_on_exception(self, mock_keyboard):
        """Should return False and not raise on error."""
        mock_keyboard.press_and_release.side_effect = Exception("Keyboard error")

        result = perform_correction(3, "the")

        assert result is False

    @patch("custom_autocorrect.correction.keyboard")
    def test_backspaces_before_write(self, mock_keyboard):
        """Should send backspaces before writing."""
        perform_correction(2, "an")

        # Get call order
        calls = mock_keyboard.method_calls
        press_indices = [
            i for i, c in enumerate(calls)
            if c[0] == "press_and_release"
        ]
        write_indices = [
            i for i, c in enumerate(calls)
            if c[0] == "write"
        ]

        # All backspaces should come before write
        assert all(p < write_indices[0] for p in press_indices)

    @patch("custom_autocorrect.correction.keyboard", None)
    def test_returns_false_if_keyboard_unavailable(self):
        """Should return False if keyboard library not available."""
        # Temporarily set keyboard to None
        import custom_autocorrect.correction as correction_module
        original_keyboard = correction_module.keyboard
        correction_module.keyboard = None

        try:
            result = perform_correction(3, "the")
            assert result is False
        finally:
            correction_module.keyboard = original_keyboard


# =============================================================================
# Tests for CorrectionEngine class
# =============================================================================


class TestCorrectionEngine:
    """Tests for the CorrectionEngine class."""

    def test_initialization_default_delay(self):
        """Engine initializes with default delay of 0."""
        engine = CorrectionEngine()
        assert engine.delay_ms == 0

    def test_initialization_custom_delay(self):
        """Engine accepts custom delay."""
        engine = CorrectionEngine(delay_ms=10)
        assert engine.delay_ms == 10

    def test_delay_setter(self):
        """Delay can be changed after initialization."""
        engine = CorrectionEngine()
        engine.delay_ms = 50
        assert engine.delay_ms == 50

    def test_delay_rejects_negative(self):
        """Delay setter rejects negative values."""
        engine = CorrectionEngine()
        with pytest.raises(ValueError, match="non-negative"):
            engine.delay_ms = -1

    def test_correction_count_starts_at_zero(self):
        """Correction count starts at zero."""
        engine = CorrectionEngine()
        assert engine.correction_count == 0

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_applies_lowercase_casing(self, mock_keyboard):
        """correct() applies lowercase casing."""
        engine = CorrectionEngine()
        engine.correct("teh", "the")

        mock_keyboard.write.assert_called_once_with("the ")

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_applies_uppercase_casing(self, mock_keyboard):
        """correct() applies uppercase casing."""
        engine = CorrectionEngine()
        engine.correct("TEH", "the")

        mock_keyboard.write.assert_called_once_with("THE ")

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_applies_capitalized_casing(self, mock_keyboard):
        """correct() applies capitalized casing."""
        engine = CorrectionEngine()
        engine.correct("Teh", "the")

        mock_keyboard.write.assert_called_once_with("The ")

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_returns_true_on_success(self, mock_keyboard):
        """correct() returns True on success."""
        engine = CorrectionEngine()
        result = engine.correct("teh", "the")
        assert result is True

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_increments_count_on_success(self, mock_keyboard):
        """correct() increments correction count on success."""
        engine = CorrectionEngine()
        assert engine.correction_count == 0

        engine.correct("teh", "the")
        assert engine.correction_count == 1

        engine.correct("adn", "and")
        assert engine.correction_count == 2

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_returns_false_on_error(self, mock_keyboard):
        """correct() returns False on keyboard error."""
        mock_keyboard.press_and_release.side_effect = Exception("Error")

        engine = CorrectionEngine()
        result = engine.correct("teh", "the")
        assert result is False

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_does_not_increment_on_error(self, mock_keyboard):
        """correct() does not increment count on error."""
        mock_keyboard.press_and_release.side_effect = Exception("Error")

        engine = CorrectionEngine()
        engine.correct("teh", "the")
        assert engine.correction_count == 0

    def test_correct_returns_false_for_empty_original(self):
        """correct() returns False for empty original word."""
        engine = CorrectionEngine()
        result = engine.correct("", "the")
        assert result is False

    def test_correct_returns_false_for_empty_correction(self):
        """correct() returns False for empty correction."""
        engine = CorrectionEngine()
        result = engine.correct("teh", "")
        assert result is False

    @patch("custom_autocorrect.correction.keyboard")
    def test_reset_count(self, mock_keyboard):
        """reset_count() resets correction counter."""
        engine = CorrectionEngine()
        engine.correct("teh", "the")
        engine.correct("adn", "and")
        assert engine.correction_count == 2

        engine.reset_count()
        assert engine.correction_count == 0

    @patch("custom_autocorrect.correction.keyboard")
    def test_correct_sends_correct_backspaces(self, mock_keyboard):
        """correct() sends correct number of backspaces."""
        engine = CorrectionEngine()
        engine.correct("teh", "the")

        # 3 chars + 1 space = 4 backspaces
        backspace_calls = [
            c for c in mock_keyboard.press_and_release.call_args_list
            if c == call("backspace")
        ]
        assert len(backspace_calls) == 4


# =============================================================================
# Integration tests
# =============================================================================


class TestCorrectionIntegration:
    """Integration tests for the correction system."""

    @patch("custom_autocorrect.correction.keyboard")
    def test_full_correction_flow_lowercase(self, mock_keyboard):
        """Full correction flow for lowercase word."""
        engine = CorrectionEngine()
        result = engine.correct("teh", "the")

        assert result is True
        assert engine.correction_count == 1

        # Verify backspaces (4 = 3 chars + 1 space)
        backspace_calls = [
            c for c in mock_keyboard.press_and_release.call_args_list
            if c == call("backspace")
        ]
        assert len(backspace_calls) == 4

        # Verify correction typed
        mock_keyboard.write.assert_called_once_with("the ")

    @patch("custom_autocorrect.correction.keyboard")
    def test_full_correction_flow_capitalized(self, mock_keyboard):
        """Full correction flow for capitalized word."""
        engine = CorrectionEngine()
        result = engine.correct("Teh", "the")

        assert result is True
        mock_keyboard.write.assert_called_once_with("The ")

    @patch("custom_autocorrect.correction.keyboard")
    def test_multiple_corrections(self, mock_keyboard):
        """Multiple corrections in sequence."""
        engine = CorrectionEngine()

        engine.correct("teh", "the")
        engine.correct("ADN", "and")
        engine.correct("Hte", "the")

        assert engine.correction_count == 3

        # Check the write calls
        write_calls = mock_keyboard.write.call_args_list
        assert write_calls[0] == call("the ")
        assert write_calls[1] == call("AND ")
        assert write_calls[2] == call("The ")
