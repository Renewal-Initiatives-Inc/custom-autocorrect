"""Unit tests for the KeystrokeEngine class.

These tests use the simulate_key method to test the engine logic without
requiring actual keyboard hooks. Integration tests with real keyboard
input should be run on Windows.
"""

import pytest

from custom_autocorrect.keystroke_engine import KeystrokeEngine


class TestKeystrokeEngineBasics:
    """Basic functionality tests for KeystrokeEngine."""

    def test_engine_initializes_with_empty_buffer(self):
        """New engine should have empty buffer."""
        engine = KeystrokeEngine()
        assert engine.buffer.is_empty()
        assert not engine.is_running

    def test_engine_accepts_callback(self):
        """Engine should accept a callback function."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)
        assert engine.buffer.is_empty()

    def test_engine_not_running_initially(self):
        """Engine should not be running when created."""
        engine = KeystrokeEngine()
        assert not engine.is_running


class TestKeystrokeEngineSimulation:
    """Tests using simulated key events."""

    def test_regular_keys_added_to_buffer(self):
        """Regular character keys should be added to buffer."""
        engine = KeystrokeEngine()

        engine.simulate_key("h")
        engine.simulate_key("e")
        engine.simulate_key("l")
        engine.simulate_key("l")
        engine.simulate_key("o")

        assert engine.buffer.get_word() == "hello"

    def test_space_completes_word(self):
        """Space should complete word and trigger callback."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in "hello":
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == ["hello"]
        assert engine.buffer.is_empty()

    def test_space_on_empty_buffer_no_callback(self):
        """Space on empty buffer should not trigger callback."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        engine.simulate_key("space")

        assert words == []

    def test_backspace_removes_character(self):
        """Backspace should remove last character."""
        engine = KeystrokeEngine()

        for char in "hello":
            engine.simulate_key(char)
        engine.simulate_key("backspace")

        assert engine.buffer.get_word() == "hell"

    def test_backspace_on_empty_buffer_safe(self):
        """Backspace on empty buffer should be safe."""
        engine = KeystrokeEngine()
        engine.simulate_key("backspace")  # Should not raise
        assert engine.buffer.is_empty()

    def test_enter_clears_buffer(self):
        """Enter should clear the buffer without triggering callback."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in "hello":
            engine.simulate_key(char)
        engine.simulate_key("enter")

        assert words == []  # No word completed
        assert engine.buffer.is_empty()

    def test_tab_clears_buffer(self):
        """Tab should clear the buffer."""
        engine = KeystrokeEngine()

        for char in "hello":
            engine.simulate_key(char)
        engine.simulate_key("tab")

        assert engine.buffer.is_empty()

    def test_escape_clears_buffer(self):
        """Escape should clear the buffer."""
        engine = KeystrokeEngine()

        for char in "hello":
            engine.simulate_key(char)
        engine.simulate_key("escape")

        assert engine.buffer.is_empty()

    def test_arrow_keys_clear_buffer(self):
        """Arrow keys should clear the buffer."""
        for arrow in ["up", "down", "left", "right"]:
            engine = KeystrokeEngine()

            for char in "hello":
                engine.simulate_key(char)
            engine.simulate_key(arrow)

            assert engine.buffer.is_empty(), f"{arrow} should clear buffer"


class TestKeystrokeEngineModifierKeys:
    """Tests for modifier key handling."""

    def test_shift_ignored(self):
        """Shift alone should be ignored."""
        engine = KeystrokeEngine()

        engine.simulate_key("shift")

        assert engine.buffer.is_empty()

    def test_ctrl_ignored(self):
        """Ctrl alone should be ignored."""
        engine = KeystrokeEngine()

        engine.simulate_key("ctrl")

        assert engine.buffer.is_empty()

    def test_alt_ignored(self):
        """Alt alone should be ignored."""
        engine = KeystrokeEngine()

        engine.simulate_key("alt")

        assert engine.buffer.is_empty()

    def test_left_shift_ignored(self):
        """Left shift should be ignored."""
        engine = KeystrokeEngine()

        engine.simulate_key("left shift")

        assert engine.buffer.is_empty()

    def test_caps_lock_ignored(self):
        """Caps lock should be ignored."""
        engine = KeystrokeEngine()

        engine.simulate_key("caps lock")

        assert engine.buffer.is_empty()


class TestKeystrokeEngineCapitalization:
    """Tests for uppercase character handling."""

    def test_uppercase_letters_preserved(self):
        """Uppercase letters should be preserved."""
        engine = KeystrokeEngine()

        engine.simulate_key("H")
        engine.simulate_key("e")
        engine.simulate_key("l")
        engine.simulate_key("l")
        engine.simulate_key("o")

        assert engine.buffer.get_word() == "Hello"

    def test_all_uppercase(self):
        """All uppercase should be preserved."""
        engine = KeystrokeEngine()

        for char in "HELLO":
            engine.simulate_key(char)

        assert engine.buffer.get_word() == "HELLO"

    def test_mixed_case(self):
        """Mixed case should be preserved."""
        engine = KeystrokeEngine()

        for char in "HeLLo":
            engine.simulate_key(char)

        assert engine.buffer.get_word() == "HeLLo"


class TestKeystrokeEngineKeyUpIgnored:
    """Tests that key up events are ignored."""

    def test_key_up_ignored(self):
        """Key up events should be ignored."""
        engine = KeystrokeEngine()

        engine.simulate_key("h", "down")
        engine.simulate_key("h", "up")  # Should be ignored
        engine.simulate_key("e", "down")

        assert engine.buffer.get_word() == "he"


class TestKeystrokeEngineMultipleWords:
    """Tests for handling multiple words."""

    def test_multiple_words(self):
        """Multiple words should be captured separately."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        # Type "hello world"
        for char in "hello":
            engine.simulate_key(char)
        engine.simulate_key("space")

        for char in "world":
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == ["hello", "world"]

    def test_word_with_numbers(self):
        """Words with numbers should be captured."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in "test123":
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == ["test123"]


class TestKeystrokeEngineCallbackErrors:
    """Tests for callback error handling."""

    def test_callback_error_doesnt_crash(self):
        """Errors in callback should not crash the engine."""

        def bad_callback(word):
            raise ValueError("Intentional test error")

        engine = KeystrokeEngine(on_word_complete=bad_callback)

        for char in "hello":
            engine.simulate_key(char)

        # Should not raise - error is logged but not propagated
        engine.simulate_key("space")

        # Buffer should still be cleared
        assert engine.buffer.is_empty()


class TestKeystrokeEngineIntegration:
    """Integration-style tests simulating real usage patterns."""

    def test_typing_with_correction(self):
        """Simulate typing with a typo and correction."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        # Type "helllo" (typo)
        for char in "helllo":
            engine.simulate_key(char)

        # Backspace twice and retype
        engine.simulate_key("backspace")
        engine.simulate_key("backspace")
        engine.simulate_key("o")

        # Complete word
        engine.simulate_key("space")

        assert words == ["hello"]

    def test_partial_word_then_enter(self):
        """Typing partial word then Enter should not emit word."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in "partial":
            engine.simulate_key(char)
        engine.simulate_key("enter")

        assert words == []

        for char in "newword":
            engine.simulate_key(char)
        engine.simulate_key("space")

        assert words == ["newword"]
