"""Unit tests for the WordBuffer class.

These tests verify the character accumulation logic that forms the foundation
of word detection in Phase 2.
"""

import pytest

from custom_autocorrect.word_buffer import WordBuffer


class TestWordBufferBasics:
    """Basic functionality tests for WordBuffer."""

    def test_empty_buffer_returns_empty_string(self):
        """New buffer should return empty string."""
        buffer = WordBuffer()
        assert buffer.get_word() == ""
        assert buffer.is_empty()
        assert len(buffer) == 0

    def test_add_single_character(self):
        """Adding one character should be retrievable."""
        buffer = WordBuffer()
        buffer.add_character("a")
        assert buffer.get_word() == "a"
        assert len(buffer) == 1
        assert not buffer.is_empty()

    def test_add_multiple_characters(self):
        """Characters accumulate in order."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        assert buffer.get_word() == "hello"
        assert len(buffer) == 5

    def test_add_empty_string_is_noop(self):
        """Adding empty string should not change buffer."""
        buffer = WordBuffer()
        buffer.add_character("")
        assert buffer.get_word() == ""
        assert buffer.is_empty()

    def test_add_multichar_string_uses_first_only(self):
        """Adding multiple chars should only use the first."""
        buffer = WordBuffer()
        buffer.add_character("abc")
        assert buffer.get_word() == "a"


class TestWordBufferBackspace:
    """Tests for backspace/remove functionality."""

    def test_remove_last_character(self):
        """Backspace removes last character."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        buffer.remove_last()
        assert buffer.get_word() == "hell"
        assert len(buffer) == 4

    def test_remove_multiple_characters(self):
        """Multiple backspaces remove multiple characters."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        buffer.remove_last()
        buffer.remove_last()
        assert buffer.get_word() == "hel"

    def test_remove_last_on_empty_buffer_is_safe(self):
        """Backspace on empty buffer is safe (no-op)."""
        buffer = WordBuffer()
        buffer.remove_last()  # Should not raise
        assert buffer.get_word() == ""
        assert buffer.is_empty()

    def test_remove_all_characters_empties_buffer(self):
        """Removing all characters should result in empty buffer."""
        buffer = WordBuffer()
        for char in "hi":
            buffer.add_character(char)
        buffer.remove_last()
        buffer.remove_last()
        assert buffer.is_empty()


class TestWordBufferClear:
    """Tests for clear functionality."""

    def test_clear_empties_buffer(self):
        """Clear empties the buffer."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        buffer.clear()
        assert buffer.get_word() == ""
        assert buffer.is_empty()
        assert len(buffer) == 0

    def test_clear_empty_buffer_is_safe(self):
        """Clearing empty buffer is safe."""
        buffer = WordBuffer()
        buffer.clear()  # Should not raise
        assert buffer.is_empty()

    def test_buffer_usable_after_clear(self):
        """Buffer should be reusable after clear."""
        buffer = WordBuffer()
        buffer.add_character("a")
        buffer.clear()
        buffer.add_character("b")
        assert buffer.get_word() == "b"


class TestWordBufferSpecialCharacters:
    """Tests for special character handling."""

    def test_unicode_characters(self):
        """Buffer handles unicode characters."""
        buffer = WordBuffer()
        for char in "cafe":
            buffer.add_character(char)
        buffer.add_character("\u0301")  # Combining acute accent
        assert len(buffer) == 5

    def test_unicode_word(self):
        """Buffer handles unicode words."""
        buffer = WordBuffer()
        for char in "naïve":
            buffer.add_character(char)
        assert buffer.get_word() == "naïve"

    def test_mixed_case_preserved(self):
        """Buffer preserves character casing."""
        buffer = WordBuffer()
        for char in "HeLLo":
            buffer.add_character(char)
        assert buffer.get_word() == "HeLLo"

    def test_numbers_supported(self):
        """Buffer accepts numbers."""
        buffer = WordBuffer()
        for char in "test123":
            buffer.add_character(char)
        assert buffer.get_word() == "test123"

    def test_punctuation_supported(self):
        """Buffer accepts punctuation."""
        buffer = WordBuffer()
        for char in "don't":
            buffer.add_character(char)
        assert buffer.get_word() == "don't"


class TestWordBufferIteration:
    """Tests for iteration support."""

    def test_iterate_over_characters(self):
        """Can iterate over buffer characters."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        chars = list(buffer)
        assert chars == ["h", "e", "l", "l", "o"]

    def test_iterate_empty_buffer(self):
        """Iterating empty buffer yields nothing."""
        buffer = WordBuffer()
        chars = list(buffer)
        assert chars == []


class TestWordBufferRepr:
    """Tests for string representation."""

    def test_repr_empty(self):
        """Empty buffer has appropriate repr."""
        buffer = WordBuffer()
        assert repr(buffer) == "WordBuffer('')"

    def test_repr_with_content(self):
        """Buffer with content shows in repr."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        assert repr(buffer) == "WordBuffer('hello')"


class TestWordBufferIntegration:
    """Integration-style tests simulating real usage patterns."""

    def test_typical_word_typing(self):
        """Simulate typing a word character by character."""
        buffer = WordBuffer()

        # Type "hello"
        buffer.add_character("h")
        buffer.add_character("e")
        buffer.add_character("l")
        buffer.add_character("l")
        buffer.add_character("o")

        assert buffer.get_word() == "hello"

    def test_word_with_correction(self):
        """Simulate typing with a typo and correction."""
        buffer = WordBuffer()

        # Type "helllo" (typo)
        for char in "helllo":
            buffer.add_character(char)

        # Backspace twice
        buffer.remove_last()
        buffer.remove_last()

        # Type "o"
        buffer.add_character("o")

        assert buffer.get_word() == "hello"

    def test_multiple_words_with_clear(self):
        """Simulate typing multiple words (clearing between them)."""
        buffer = WordBuffer()
        words = []

        # Type "hello"
        for char in "hello":
            buffer.add_character(char)
        words.append(buffer.get_word())
        buffer.clear()

        # Type "world"
        for char in "world":
            buffer.add_character(char)
        words.append(buffer.get_word())
        buffer.clear()

        assert words == ["hello", "world"]
