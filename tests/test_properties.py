"""Property-based tests for Custom Autocorrect using Hypothesis.

These tests verify correctness properties that should hold across all valid inputs,
as defined in design.md's Correctness Properties section.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings

from custom_autocorrect.word_buffer import WordBuffer
from custom_autocorrect.keystroke_engine import KeystrokeEngine


# Strategy for generating valid word characters (letters and numbers)
word_chars = st.characters(
    whitelist_categories=["Lu", "Ll", "Nd"],  # Uppercase, lowercase, digits
    min_codepoint=32,
    max_codepoint=126,
)

# Strategy for generating word-like strings
word_text = st.text(alphabet=word_chars, min_size=1, max_size=50)


class TestWordBufferProperties:
    """Property-based tests for WordBuffer."""

    @given(word_text)
    def test_add_all_chars_recovers_original(self, text: str):
        """Adding all chars of a string should recover that string."""
        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)
        assert buffer.get_word() == text

    @given(word_text)
    def test_length_equals_char_count(self, text: str):
        """Buffer length should equal number of added characters."""
        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)
        assert len(buffer) == len(text)

    @given(word_text)
    def test_remove_all_chars_empties_buffer(self, text: str):
        """Removing all chars should empty the buffer."""
        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)
        for _ in text:
            buffer.remove_last()
        assert buffer.is_empty()
        assert buffer.get_word() == ""

    @given(st.integers(min_value=0, max_value=100))
    def test_extra_removes_are_safe(self, extra_removes: int):
        """Removing more chars than exist should be safe."""
        buffer = WordBuffer()
        buffer.add_character("a")
        for _ in range(1 + extra_removes):
            buffer.remove_last()
        assert buffer.is_empty()

    @given(word_text, st.integers(min_value=1, max_value=10))
    def test_partial_remove_preserves_prefix(self, text: str, remove_count: int):
        """Removing n chars should leave the first len-n chars."""
        assume(len(text) > remove_count)

        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)

        for _ in range(remove_count):
            buffer.remove_last()

        expected = text[:-remove_count]
        assert buffer.get_word() == expected

    @given(word_text)
    def test_clear_then_add_works(self, text: str):
        """After clearing, buffer should accept new input normally."""
        buffer = WordBuffer()

        # Add some text
        for char in text:
            buffer.add_character(char)

        # Clear
        buffer.clear()
        assert buffer.is_empty()

        # Add different text
        for char in "newtext":
            buffer.add_character(char)

        assert buffer.get_word() == "newtext"

    @given(word_text)
    def test_iteration_returns_all_chars(self, text: str):
        """Iterating buffer should return all characters in order."""
        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)

        chars = list(buffer)
        assert chars == list(text)


class TestKeystrokeEngineProperties:
    """Property-based tests for KeystrokeEngine."""

    @given(word_text)
    def test_typing_word_and_space_emits_word(self, text: str):
        """Typing a word followed by space should emit that exact word."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in text:
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == [text]

    @given(st.lists(word_text, min_size=1, max_size=5))
    def test_multiple_words_all_captured(self, word_list: list):
        """Multiple words separated by space should all be captured."""
        captured = []
        engine = KeystrokeEngine(on_word_complete=captured.append)

        for word in word_list:
            for char in word:
                engine.simulate_key(char)
            engine.simulate_key("space")

        assert captured == word_list

    @given(word_text)
    @settings(max_examples=50)
    def test_backspace_count_matches_buffer_reduction(self, text: str):
        """Each backspace should reduce buffer length by 1."""
        engine = KeystrokeEngine()

        for char in text:
            engine.simulate_key(char)

        initial_len = len(engine.buffer)
        assert initial_len == len(text)

        backspaces = min(3, len(text))
        for _ in range(backspaces):
            engine.simulate_key("backspace")

        assert len(engine.buffer) == len(text) - backspaces

    @given(word_text, st.sampled_from(["enter", "tab", "escape", "up", "down", "left", "right"]))
    def test_clear_keys_empty_buffer_without_emit(self, text: str, clear_key: str):
        """Clear keys should empty buffer without emitting word."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in text:
            engine.simulate_key(char)

        engine.simulate_key(clear_key)

        assert engine.buffer.is_empty()
        assert words == []  # No word emitted


class TestCasingPreservation:
    """Property-based tests for casing preservation (CP3 from design.md)."""

    @given(word_text)
    def test_lowercase_preserved(self, text: str):
        """Lowercase input should produce lowercase output."""
        lower_text = text.lower()
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in lower_text:
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == [lower_text]

    @given(word_text)
    def test_uppercase_preserved(self, text: str):
        """Uppercase input should produce uppercase output."""
        upper_text = text.upper()
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in upper_text:
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == [upper_text]

    @given(word_text)
    def test_original_casing_preserved(self, text: str):
        """Original mixed casing should be preserved exactly."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in text:
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == [text]
