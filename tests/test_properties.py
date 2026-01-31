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


# Strategy for generating valid rule typos (no =, no #, no whitespace-only)
rule_typo = st.text(
    alphabet=st.characters(
        whitelist_categories=["Lu", "Ll", "Nd"],
        min_codepoint=65,  # Start from 'A'
        max_codepoint=122,  # End at 'z'
    ),
    min_size=1,
    max_size=20,
).filter(lambda s: "=" not in s and not s.startswith("#") and s.strip() == s)

# Strategy for generating valid corrections
rule_correction = st.text(
    alphabet=st.characters(
        whitelist_categories=["Lu", "Ll", "Nd"],
        min_codepoint=65,
        max_codepoint=122,
    ),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip() == s)


class TestRuleIntegrityProperty:
    """Property-based tests for CP1: Rule Integrity.

    For any correction that occurs, the trigger must exactly match
    a key in rules.txt (case-insensitive matching).
    """

    @given(rule_typo, rule_correction)
    def test_match_only_if_rule_exists(self, typo: str, correction: str):
        """Matcher only returns rule if it was loaded."""
        from custom_autocorrect.rules import RuleMatcher

        assume(typo.lower() != correction.lower())  # Valid rule

        matcher = RuleMatcher()
        # Don't load any rules

        # Should not match anything
        assert matcher.match(typo) is None

    @given(rule_typo, rule_correction)
    @settings(max_examples=50)
    def test_match_returns_exact_loaded_rule(self, typo: str, correction: str):
        """Match returns the exact rule that was loaded."""
        import tempfile
        from pathlib import Path
        from custom_autocorrect.rules import RuleMatcher

        assume(typo.lower() != correction.lower())

        # Create temporary rules file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(f"{typo}={correction}\n")
            path = Path(f.name)

        try:
            matcher = RuleMatcher(rules_path=path)
            matcher.load()

            # Match should return exactly what we put in
            rule = matcher.match(typo)
            assert rule is not None
            assert rule.correction == correction
        finally:
            path.unlink()

    @given(st.lists(st.tuples(rule_typo, rule_correction), min_size=1, max_size=10))
    @settings(max_examples=30)
    def test_all_loaded_rules_match(self, rules: list):
        """All loaded rules should be matchable."""
        import tempfile
        from pathlib import Path
        from custom_autocorrect.rules import RuleMatcher

        # Filter to valid rules (typo != correction) and unique typos
        seen_typos = set()
        valid_rules = []
        for t, c in rules:
            if t.lower() != c.lower() and t.lower() not in seen_typos:
                valid_rules.append((t, c))
                seen_typos.add(t.lower())

        assume(len(valid_rules) > 0)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            for typo, correction in valid_rules:
                f.write(f"{typo}={correction}\n")
            path = Path(f.name)

        try:
            matcher = RuleMatcher(rules_path=path)
            matcher.load()

            for typo, _ in valid_rules:
                assert matcher.match(typo) is not None
        finally:
            path.unlink()

    @given(rule_typo)
    def test_non_existent_rule_never_matches(self, word: str):
        """Words without rules should never match."""
        import tempfile
        from pathlib import Path
        from custom_autocorrect.rules import RuleMatcher

        # Create a rules file WITHOUT this word
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("teh=the\nadn=and\n")
            path = Path(f.name)

        try:
            matcher = RuleMatcher(rules_path=path)
            matcher.load()

            # If word is not one of our rules, it shouldn't match
            if word.lower() not in ["teh", "adn"]:
                assert matcher.match(word) is None
        finally:
            path.unlink()


class TestWholeWordProperty:
    """Property-based tests for CP2: Whole-Word Guarantee.

    Note: This is already satisfied by KeystrokeEngine's word extraction.
    The RuleMatcher only sees complete words, never substrings.
    These tests verify the integration works correctly.
    """

    @given(word_text)
    def test_engine_emits_complete_words_only(self, text: str):
        """Engine emits the complete word, not substrings."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        for char in text:
            engine.simulate_key(char)
        engine.simulate_key("space")

        # The only word emitted is the complete word
        assert words == [text]

    @given(word_text, word_text)
    def test_typing_without_space_does_not_emit(self, prefix: str, suffix: str):
        """Typing without space should not emit any words."""
        words = []
        engine = KeystrokeEngine(on_word_complete=words.append)

        # Type prefix + suffix without any space
        for char in prefix + suffix:
            engine.simulate_key(char)

        # No words should be emitted yet
        assert words == []

        # Now press space
        engine.simulate_key("space")

        # Now we should get the complete word
        assert words == [prefix + suffix]
