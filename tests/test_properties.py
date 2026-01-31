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


# Strategy for generating alphabetic-only strings (for casing tests)
alpha_text = st.text(
    alphabet=st.characters(
        whitelist_categories=["Lu", "Ll"],  # Uppercase and lowercase letters only
        min_codepoint=65,  # Start from 'A'
        max_codepoint=122,  # End at 'z'
    ),
    min_size=1,
    max_size=20,
).filter(lambda s: s.isalpha())

# Strategy for multi-character alphabetic strings (needed for capitalized tests)
# Single chars like "A" are ambiguous - uppercase and capitalized look the same
alpha_text_multi = st.text(
    alphabet=st.characters(
        whitelist_categories=["Lu", "Ll"],
        min_codepoint=65,
        max_codepoint=122,
    ),
    min_size=2,  # At least 2 chars to distinguish capitalized from uppercase
    max_size=20,
).filter(lambda s: s.isalpha())


class TestCasingPreservationCP3:
    """Property-based tests for CP3: Casing Preservation.

    For any correction where trigger has casing pattern P,
    the correction shall have the same casing pattern P.

    These tests verify the correction module's casing functions.
    """

    @given(alpha_text, alpha_text)
    def test_lowercase_input_produces_lowercase_output(self, original: str, correction: str):
        """CP3: lowercase input produces lowercase output."""
        from custom_autocorrect.correction import apply_casing

        lower_original = original.lower()
        result = apply_casing(lower_original, correction)

        assert result == result.lower(), f"Expected lowercase output for '{lower_original}' -> '{correction}'"

    @given(alpha_text, alpha_text)
    def test_uppercase_input_produces_uppercase_output(self, original: str, correction: str):
        """CP3: uppercase input produces uppercase output."""
        from custom_autocorrect.correction import apply_casing

        upper_original = original.upper()
        result = apply_casing(upper_original, correction)

        assert result == result.upper(), f"Expected uppercase output for '{upper_original}' -> '{correction}'"

    @given(alpha_text_multi, alpha_text)
    def test_capitalized_input_produces_capitalized_output(self, original: str, correction: str):
        """CP3: capitalized input produces capitalized output.

        Note: Uses alpha_text_multi (2+ chars) because single uppercase letters
        like "A" are ambiguous - they look the same capitalized or uppercase.
        """
        from custom_autocorrect.correction import apply_casing

        cap_original = original.capitalize()
        result = apply_casing(cap_original, correction)

        # Capitalize means first letter upper, rest lower
        assert result == result.capitalize(), f"Expected capitalized output for '{cap_original}' -> '{correction}'"

    @given(alpha_text_multi, alpha_text_multi)
    def test_detect_casing_pattern_consistent(self, word1: str, word2: str):
        """detect_casing_pattern is consistent for same casing.

        Note: Uses alpha_text_multi (2+ chars) because single uppercase letters
        like "A" are detected as "uppercase", not "capitalized".
        """
        from custom_autocorrect.correction import detect_casing_pattern

        # Same casing pattern should produce same result
        lower1 = word1.lower()
        lower2 = word2.lower()
        assert detect_casing_pattern(lower1) == detect_casing_pattern(lower2) == "lowercase"

        upper1 = word1.upper()
        upper2 = word2.upper()
        assert detect_casing_pattern(upper1) == detect_casing_pattern(upper2) == "uppercase"

        cap1 = word1.capitalize()
        cap2 = word2.capitalize()
        assert detect_casing_pattern(cap1) == detect_casing_pattern(cap2) == "capitalized"

    @given(alpha_text, alpha_text)
    def test_apply_casing_never_crashes(self, original: str, correction: str):
        """apply_casing should never raise for any alphabetic inputs."""
        from custom_autocorrect.correction import apply_casing

        # Should not raise for any input combination
        result = apply_casing(original, correction)
        assert isinstance(result, str)

        # Also test with modified casings
        result = apply_casing(original.lower(), correction)
        assert isinstance(result, str)

        result = apply_casing(original.upper(), correction)
        assert isinstance(result, str)

        result = apply_casing(original.capitalize(), correction)
        assert isinstance(result, str)

    @given(alpha_text, alpha_text)
    @settings(max_examples=50)
    def test_casing_idempotent_for_standard_patterns(self, original: str, correction: str):
        """Applying casing twice gives same result for standard patterns."""
        from custom_autocorrect.correction import apply_casing, detect_casing_pattern

        # For standard patterns (not mixed), applying casing is idempotent
        for transform in [str.lower, str.upper, str.capitalize]:
            transformed_original = transform(original)
            result1 = apply_casing(transformed_original, correction)
            result2 = apply_casing(transformed_original, result1)
            # Pattern should be preserved
            assert detect_casing_pattern(result1) == detect_casing_pattern(result2)

    @given(st.text(min_size=0, max_size=50))
    def test_detect_casing_pattern_never_crashes(self, text: str):
        """detect_casing_pattern should never raise for any input."""
        from custom_autocorrect.correction import detect_casing_pattern

        # Should not raise for any input
        result = detect_casing_pattern(text)
        assert result in ("lowercase", "uppercase", "capitalized", "mixed")

    @given(alpha_text)
    def test_empty_correction_returns_empty(self, original: str):
        """Empty correction string returns empty."""
        from custom_autocorrect.correction import apply_casing

        result = apply_casing(original, "")
        assert result == ""

    @given(alpha_text)
    def test_empty_original_returns_correction_as_is(self, correction: str):
        """Empty original string returns correction as-is."""
        from custom_autocorrect.correction import apply_casing

        result = apply_casing("", correction)
        assert result == correction


class TestLogRotationCP5:
    """Property-based tests for CP5: Log Rotation.

    For any state of corrections.log, the file shall contain at most
    MAX_LOG_ENTRIES entries.
    """

    @given(st.integers(min_value=0, max_value=500))
    def test_rotation_never_exceeds_max(self, num_entries: int):
        """CP5: Log rotation always produces <= MAX_LOG_ENTRIES."""
        from custom_autocorrect.correction_log import rotate_log, MAX_LOG_ENTRIES

        entries = [f"entry_{i}" for i in range(num_entries)]
        rotated = rotate_log(entries)

        assert len(rotated) <= MAX_LOG_ENTRIES

    @given(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=300))
    def test_rotation_preserves_newest(self, entries: list):
        """CP5: Rotation keeps the newest entries."""
        from custom_autocorrect.correction_log import rotate_log, MAX_LOG_ENTRIES

        rotated = rotate_log(entries)

        if len(entries) > MAX_LOG_ENTRIES:
            assert rotated == entries[-MAX_LOG_ENTRIES:]
        else:
            assert rotated == entries

    @given(st.integers(min_value=101, max_value=500))
    def test_large_sequences_handled(self, num_corrections: int):
        """CP5: Simulating many corrections keeps log bounded."""
        from custom_autocorrect.correction_log import rotate_log, MAX_LOG_ENTRIES

        # Simulate num_corrections being logged one at a time
        entries = []
        for i in range(num_corrections):
            entries.append(f"2026-01-31 00:00:{i:02d} | typo{i} \u2192 fix{i} | Window")
            entries = rotate_log(entries)

        assert len(entries) <= MAX_LOG_ENTRIES

    @given(st.integers(min_value=0, max_value=100))
    def test_under_limit_unchanged(self, num_entries: int):
        """CP5: Entries at or under limit are not modified."""
        from custom_autocorrect.correction_log import rotate_log, MAX_LOG_ENTRIES

        entries = [f"entry_{i}" for i in range(num_entries)]
        rotated = rotate_log(entries)

        if num_entries <= MAX_LOG_ENTRIES:
            assert rotated == entries

    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=200))
    def test_rotation_preserves_order(self, entries: list):
        """CP5: Rotation preserves order of kept entries."""
        from custom_autocorrect.correction_log import rotate_log, MAX_LOG_ENTRIES

        rotated = rotate_log(entries)

        # Check order is preserved (newest entries kept)
        if len(entries) > MAX_LOG_ENTRIES:
            expected_start = len(entries) - MAX_LOG_ENTRIES
            for i, entry in enumerate(rotated):
                assert entry == entries[expected_start + i]

    @given(st.integers(min_value=1, max_value=50))
    def test_custom_max_entries_respected(self, max_entries: int):
        """CP5: Custom max_entries parameter is respected."""
        from custom_autocorrect.correction_log import rotate_log

        # Create more entries than the limit
        entries = [f"entry_{i}" for i in range(max_entries * 2)]
        rotated = rotate_log(entries, max_entries=max_entries)

        assert len(rotated) == max_entries
        # Should have the newest entries
        assert rotated == entries[-max_entries:]
