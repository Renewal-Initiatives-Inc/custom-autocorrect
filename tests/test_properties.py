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


class TestPasswordFieldSafetyCP7:
    """Property-based tests for CP7: Password Field Safety.

    For any detected password field, no correction shall occur.
    """

    @given(word_text)
    def test_no_correction_in_password_field(self, word: str):
        """CP7: When password field detected, correction is never called."""
        from unittest.mock import patch, MagicMock
        from custom_autocorrect.main import on_word_detected
        from custom_autocorrect.rules import Rule

        with patch("custom_autocorrect.main.is_password_field", return_value=True):
            with patch("custom_autocorrect.main._correction_engine") as mock_engine:
                with patch("custom_autocorrect.main._matcher") as mock_matcher:
                    # Set up matcher to return a rule (would trigger correction)
                    mock_matcher.match.return_value = Rule(word.lower(), "corrected", word.lower())
                    mock_engine.correct = MagicMock()

                    # Call with the word
                    on_word_detected(word)

                    # Correction should NOT have been called
                    mock_engine.correct.assert_not_called()

    @given(word_text)
    def test_is_password_field_always_returns_bool(self, word: str):
        """CP7: is_password_field always returns a boolean, never raises."""
        from custom_autocorrect.password_detect import is_password_field, reset_uia_cache

        # Reset cache to ensure fresh test
        reset_uia_cache()

        result = is_password_field()
        assert isinstance(result, bool)

    @given(word_text)
    def test_correction_proceeds_when_not_password_field(self, word: str):
        """CP7: When not a password field, normal correction flow proceeds."""
        from unittest.mock import patch, MagicMock
        from custom_autocorrect.main import on_word_detected
        from custom_autocorrect.rules import Rule

        with patch("custom_autocorrect.main.is_password_field", return_value=False):
            with patch("custom_autocorrect.main._correction_engine") as mock_engine:
                with patch("custom_autocorrect.main._matcher") as mock_matcher:
                    with patch("custom_autocorrect.main.log_correction"):
                        # Set up matcher to return a rule
                        mock_matcher.match.return_value = Rule(word.lower(), "corrected", word.lower())
                        mock_engine.correct.return_value = True

                        # Call with the word
                        on_word_detected(word)

                        # Correction SHOULD have been called
                        mock_engine.correct.assert_called_once()

    @given(st.sampled_from([
        Exception("Generic error"),
        RuntimeError("Runtime error"),
        OSError("OS error"),
        AttributeError("Attribute error"),
    ]))
    def test_password_detection_error_allows_correction(self, error: Exception):
        """CP7: Password detection error should allow corrections (fail-safe)."""
        from unittest.mock import patch
        from custom_autocorrect.password_detect import is_password_field, reset_uia_cache

        reset_uia_cache()

        with patch(
            "custom_autocorrect.password_detect._get_focused_element",
            side_effect=error
        ):
            # Should return False (not True which would block corrections)
            result = is_password_field()
            assert result is False


class TestCorrectionPatternThresholdCP4:
    """Property-based tests for CP4: Correction Pattern Threshold.

    For any pattern appearing in suggestions.txt, that pattern must represent
    a word the user typed, deleted via backspace, and replaced with a different
    word, at least SUGGESTION_THRESHOLD times.
    """

    @given(word_text, word_text, st.integers(min_value=1, max_value=4))
    def test_pattern_not_suggested_before_threshold(self, w1: str, w2: str, count: int):
        """CP4: Patterns below threshold should not be in suggestions."""
        from custom_autocorrect.suggestions import (
            CorrectionPatternTracker,
            SuggestionsFile,
            SUGGESTION_THRESHOLD,
        )

        assume(w1.lower() != w2.lower())  # Must be different words
        assume(count < SUGGESTION_THRESHOLD)  # Below threshold

        sf = SuggestionsFile()  # Memory-only
        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=SUGGESTION_THRESHOLD)

        # Record pattern count times (less than threshold)
        for _ in range(count):
            tracker.record_pattern(w1, w2)

        # Should not be in suggestions
        assert tracker.suggestion_count == 0

    @given(word_text, word_text, st.integers(min_value=5, max_value=20))
    @settings(max_examples=50)
    def test_pattern_suggested_at_or_above_threshold(self, w1: str, w2: str, count: int):
        """CP4: Patterns at or above threshold should be in suggestions."""
        import tempfile
        from pathlib import Path
        from custom_autocorrect.suggestions import (
            CorrectionPatternTracker,
            SuggestionsFile,
            SUGGESTION_THRESHOLD,
        )

        assume(w1.lower() != w2.lower())  # Must be different words
        assume(count >= SUGGESTION_THRESHOLD)  # At or above threshold

        # Need a temp file for suggestions to actually be written
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            path = Path(f.name)

        try:
            sf = SuggestionsFile(path=path)
            tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=SUGGESTION_THRESHOLD)

            # Record pattern count times (at or above threshold)
            for _ in range(count):
                tracker.record_pattern(w1, w2)

            # Should be in suggestions
            assert tracker.suggestion_count == 1
            suggestions = tracker.get_suggestions()
            assert len(suggestions) == 1
            assert suggestions[0][0] == w1.lower()
            assert suggestions[0][1] == w2.lower()
            assert suggestions[0][2] == count
        finally:
            path.unlink()

    @given(word_text)
    def test_same_word_never_tracked(self, word: str):
        """CP4: Same word (case-insensitive) should never be tracked as a pattern."""
        from custom_autocorrect.suggestions import CorrectionPatternTracker

        tracker = CorrectionPatternTracker()

        # Try recording same word with different casings
        for _ in range(10):
            result = tracker.record_pattern(word, word)
            assert result is None

        for _ in range(10):
            result = tracker.record_pattern(word.lower(), word.upper())
            assert result is None

        for _ in range(10):
            result = tracker.record_pattern(word.upper(), word.lower())
            assert result is None

    @given(word_text, word_text)
    @settings(max_examples=50)
    def test_ignored_patterns_never_suggested(self, w1: str, w2: str):
        """CP4: Ignored patterns should never appear in suggestions."""
        from custom_autocorrect.suggestions import (
            CorrectionPatternTracker,
            IgnoreList,
            SuggestionsFile,
        )

        assume(w1.lower() != w2.lower())  # Must be different words

        ignore_list = IgnoreList()
        ignore_list.add(w1, w2)

        sf = SuggestionsFile()
        tracker = CorrectionPatternTracker(
            ignore_list=ignore_list,
            suggestions_file=sf,
            threshold=1  # Low threshold to test quickly
        )

        # Try recording many times
        for _ in range(20):
            result = tracker.record_pattern(w1, w2)
            assert result is None  # Should always be ignored

        # Should never be in suggestions
        assert tracker.suggestion_count == 0

    @given(
        st.lists(st.tuples(word_text, word_text), min_size=1, max_size=10),
        st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30)
    def test_threshold_respected_for_multiple_patterns(
        self, patterns: list, threshold: int
    ):
        """CP4: Threshold should be respected for all patterns."""
        from custom_autocorrect.suggestions import (
            CorrectionPatternTracker,
            SuggestionsFile,
        )

        # Filter to valid patterns (different words) and deduplicate
        seen = set()
        valid_patterns = []
        for w1, w2 in patterns:
            key = (w1.lower(), w2.lower())
            if w1.lower() != w2.lower() and key not in seen:
                valid_patterns.append((w1, w2))
                seen.add(key)

        assume(len(valid_patterns) > 0)

        sf = SuggestionsFile()
        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=threshold)

        # Record each pattern (threshold - 1) times
        for w1, w2 in valid_patterns:
            for _ in range(threshold - 1):
                tracker.record_pattern(w1, w2)

        # None should be suggested yet
        assert tracker.suggestion_count == 0

        # Now record each one more time (reaching threshold)
        for w1, w2 in valid_patterns:
            tracker.record_pattern(w1, w2)

        # All should now be suggested
        assert tracker.suggestion_count == len(valid_patterns)

    @given(word_text, word_text, st.integers(min_value=5, max_value=15))
    @settings(max_examples=30)
    def test_suggestion_count_matches_recording_count(self, w1: str, w2: str, count: int):
        """CP4: Recorded count should match count stored in suggestion."""
        import tempfile
        from pathlib import Path
        from custom_autocorrect.suggestions import (
            CorrectionPatternTracker,
            SuggestionsFile,
            SUGGESTION_THRESHOLD,
        )

        assume(w1.lower() != w2.lower())
        assume(count >= SUGGESTION_THRESHOLD)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            path = Path(f.name)

        try:
            sf = SuggestionsFile(path=path)
            tracker = CorrectionPatternTracker(suggestions_file=sf)

            for _ in range(count):
                tracker.record_pattern(w1, w2)

            suggestions = tracker.get_suggestions()
            assert len(suggestions) == 1
            assert suggestions[0][2] == count  # Count matches
        finally:
            path.unlink()


class TestBackspacePatternDetection:
    """Property-based tests for backspace pattern detection in KeystrokeEngine."""

    @given(word_text, word_text)
    @settings(max_examples=50)
    def test_erase_and_retype_different_word_triggers_pattern(self, w1: str, w2: str):
        """Erasing a word and typing a different word should trigger pattern callback."""
        assume(w1.lower() != w2.lower())  # Must be different words
        assume(len(w1) <= 20 and len(w2) <= 20)  # Keep test fast

        patterns = []
        engine = KeystrokeEngine(
            on_correction_pattern=lambda e, r: patterns.append((e, r))
        )

        # Type first word
        for char in w1:
            engine.simulate_key(char)

        # Erase it completely
        for _ in range(len(w1)):
            engine.simulate_key("backspace")

        # Type second word
        for char in w2:
            engine.simulate_key(char)

        # Complete with space
        engine.simulate_key("space")

        assert patterns == [(w1, w2)]

    @given(word_text)
    @settings(max_examples=50)
    def test_erase_and_retype_same_word_no_pattern(self, word: str):
        """Erasing and retyping the same word should not trigger pattern callback."""
        assume(len(word) <= 20)

        patterns = []
        engine = KeystrokeEngine(
            on_correction_pattern=lambda e, r: patterns.append((e, r))
        )

        # Type word
        for char in word:
            engine.simulate_key(char)

        # Erase completely
        for _ in range(len(word)):
            engine.simulate_key("backspace")

        # Retype same word
        for char in word:
            engine.simulate_key(char)

        # Complete
        engine.simulate_key("space")

        # No pattern should be detected (same word)
        assert patterns == []

    @given(word_text, st.sampled_from(["enter", "tab", "escape", "up", "down", "left", "right"]))
    @settings(max_examples=50)
    def test_clear_key_prevents_pattern_detection(self, word: str, clear_key: str):
        """Clear keys between erase and retype should prevent pattern detection."""
        assume(len(word) <= 20)

        patterns = []
        engine = KeystrokeEngine(
            on_correction_pattern=lambda e, r: patterns.append((e, r))
        )

        # Type word
        for char in word:
            engine.simulate_key(char)

        # Erase completely
        for _ in range(len(word)):
            engine.simulate_key("backspace")

        # Press clear key
        engine.simulate_key(clear_key)

        # Type different word
        for char in "different":
            engine.simulate_key(char)

        # Complete
        engine.simulate_key("space")

        # No pattern should be detected (clear key reset tracking)
        assert patterns == []

    @given(word_text, st.integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_partial_erase_no_pattern(self, word: str, keep_chars: int):
        """Partial erase (not emptying buffer) should not set up pattern detection."""
        assume(len(word) > keep_chars)  # Ensure we can do partial erase

        patterns = []
        engine = KeystrokeEngine(
            on_correction_pattern=lambda e, r: patterns.append((e, r))
        )

        # Type word
        for char in word:
            engine.simulate_key(char)

        # Partial erase (leave some chars)
        erase_count = len(word) - keep_chars
        for _ in range(erase_count):
            engine.simulate_key("backspace")

        # Type more
        for char in "xyz":
            engine.simulate_key(char)

        # Complete
        engine.simulate_key("space")

        # No pattern should be detected (wasn't a full erase)
        assert patterns == []
