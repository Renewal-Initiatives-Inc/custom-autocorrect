"""Tests for the pattern suggestion system.

Phase 7 tests covering:
- IgnoreList: loading, checking, adding patterns
- SuggestionsFile: loading, saving, parsing format
- CorrectionPatternTracker: threshold behavior, pattern recording
"""

import pytest
from pathlib import Path
import tempfile

from custom_autocorrect.suggestions import (
    IgnoreList,
    SuggestionsFile,
    CorrectionPatternTracker,
    SUGGESTION_THRESHOLD,
    SUGGESTION_LINE_PATTERN,
)


class TestIgnoreList:
    """Tests for IgnoreList class."""

    def test_empty_ignore_list(self):
        """Empty ignore list should return 0 length."""
        ignore_list = IgnoreList()
        assert len(ignore_list) == 0

    def test_is_ignored_empty_list(self):
        """Nothing should be ignored in empty list."""
        ignore_list = IgnoreList()
        assert not ignore_list.is_ignored("teh", "the")

    def test_add_pattern_memory_only(self):
        """Adding pattern without file should work in memory."""
        ignore_list = IgnoreList()
        result = ignore_list.add("teh", "the")
        assert result is True
        assert ignore_list.is_ignored("teh", "the")
        assert len(ignore_list) == 1

    def test_is_ignored_case_insensitive(self):
        """Pattern matching should be case-insensitive."""
        ignore_list = IgnoreList()
        ignore_list.add("TEH", "THE")
        assert ignore_list.is_ignored("teh", "the")
        assert ignore_list.is_ignored("Teh", "The")
        assert ignore_list.is_ignored("TEH", "THE")

    def test_add_duplicate_pattern(self):
        """Adding duplicate pattern should succeed and not add twice."""
        ignore_list = IgnoreList()
        ignore_list.add("teh", "the")
        ignore_list.add("teh", "the")
        assert len(ignore_list) == 1

    def test_load_from_file(self, tmp_path):
        """Should load patterns from file."""
        ignore_path = tmp_path / "ignore.txt"
        ignore_path.write_text("teh=the\nadn=and\n", encoding="utf-8")

        ignore_list = IgnoreList(ignore_path=ignore_path)
        count = ignore_list.load()

        assert count == 2
        assert ignore_list.is_ignored("teh", "the")
        assert ignore_list.is_ignored("adn", "and")

    def test_load_ignores_comments(self, tmp_path):
        """Should ignore comment lines."""
        ignore_path = tmp_path / "ignore.txt"
        ignore_path.write_text("# Comment\nteh=the\n# Another comment\n", encoding="utf-8")

        ignore_list = IgnoreList(ignore_path=ignore_path)
        count = ignore_list.load()

        assert count == 1
        assert ignore_list.is_ignored("teh", "the")

    def test_load_ignores_blank_lines(self, tmp_path):
        """Should ignore blank lines."""
        ignore_path = tmp_path / "ignore.txt"
        ignore_path.write_text("teh=the\n\n\nadn=and\n", encoding="utf-8")

        ignore_list = IgnoreList(ignore_path=ignore_path)
        count = ignore_list.load()

        assert count == 2

    def test_load_handles_missing_file(self, tmp_path):
        """Should handle missing file gracefully."""
        ignore_path = tmp_path / "nonexistent.txt"
        ignore_list = IgnoreList(ignore_path=ignore_path)
        count = ignore_list.load()
        assert count == 0

    def test_add_pattern_persists(self, tmp_path):
        """Adding pattern should persist to file."""
        ignore_path = tmp_path / "ignore.txt"
        ignore_list = IgnoreList(ignore_path=ignore_path)

        ignore_list.add("teh", "the")

        # Read the file and verify
        content = ignore_path.read_text()
        assert "teh=the" in content

    def test_load_normalizes_case(self, tmp_path):
        """Loading should normalize to lowercase."""
        ignore_path = tmp_path / "ignore.txt"
        ignore_path.write_text("TEH=THE\n", encoding="utf-8")

        ignore_list = IgnoreList(ignore_path=ignore_path)
        ignore_list.load()

        # Should match regardless of input case
        assert ignore_list.is_ignored("teh", "the")


class TestSuggestionsFile:
    """Tests for SuggestionsFile class."""

    def test_empty_suggestions(self):
        """Empty suggestions file should return 0 length."""
        sf = SuggestionsFile()
        assert len(sf) == 0
        assert sf.get_all() == []

    def test_add_or_update_memory_only(self):
        """Adding suggestion without file should work in memory."""
        sf = SuggestionsFile()
        # Without a path, save returns False but memory is updated
        sf._suggestions["teh=the"] = ("the", 5)
        assert len(sf) == 1

    def test_load_parses_format(self, tmp_path):
        """Should parse suggestions file format correctly."""
        sugg_path = tmp_path / "suggestions.txt"
        sugg_path.write_text(
            "# Header\nteh=the (corrected 5 times)\nadn=and (corrected 10 times)\n",
            encoding="utf-8"
        )

        sf = SuggestionsFile(path=sugg_path)
        count = sf.load()

        assert count == 2
        suggestions = sf.get_all()
        # Should be sorted by count descending
        assert suggestions[0] == ("adn", "and", 10)
        assert suggestions[1] == ("teh", "the", 5)

    def test_load_handles_singular_time(self, tmp_path):
        """Should parse 'time' (singular) as well as 'times'."""
        sugg_path = tmp_path / "suggestions.txt"
        sugg_path.write_text("teh=the (corrected 1 time)\n", encoding="utf-8")

        sf = SuggestionsFile(path=sugg_path)
        count = sf.load()

        assert count == 1

    def test_load_ignores_comments(self, tmp_path):
        """Should ignore comment lines."""
        sugg_path = tmp_path / "suggestions.txt"
        sugg_path.write_text(
            "# Comment\nteh=the (corrected 5 times)\n",
            encoding="utf-8"
        )

        sf = SuggestionsFile(path=sugg_path)
        count = sf.load()

        assert count == 1

    def test_load_handles_missing_file(self, tmp_path):
        """Should handle missing file gracefully."""
        sugg_path = tmp_path / "nonexistent.txt"
        sf = SuggestionsFile(path=sugg_path)
        count = sf.load()
        assert count == 0

    def test_add_or_update_new(self, tmp_path):
        """Should add new suggestion."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        result = sf.add_or_update("teh", "the", 5)

        assert result is True
        assert len(sf) == 1
        # Check file was written
        content = sugg_path.read_text()
        assert "teh=the (corrected 5 times)" in content

    def test_add_or_update_existing(self, tmp_path):
        """Should update existing suggestion count."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        sf.add_or_update("teh", "the", 5)
        sf.add_or_update("teh", "the", 10)

        assert len(sf) == 1
        suggestions = sf.get_all()
        assert suggestions[0] == ("teh", "the", 10)

    def test_remove_pattern(self, tmp_path):
        """Should remove pattern from suggestions."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        sf.add_or_update("teh", "the", 5)
        sf.add_or_update("adn", "and", 6)
        sf.remove("teh", "the")

        assert len(sf) == 1
        suggestions = sf.get_all()
        assert suggestions[0][0] == "adn"

    def test_remove_nonexistent_pattern(self, tmp_path):
        """Removing nonexistent pattern should succeed."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        result = sf.remove("teh", "the")
        assert result is True

    def test_sorted_by_count(self, tmp_path):
        """Suggestions should be sorted by count descending."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        sf.add_or_update("a", "b", 3)
        sf.add_or_update("c", "d", 10)
        sf.add_or_update("e", "f", 5)

        suggestions = sf.get_all()
        counts = [s[2] for s in suggestions]
        assert counts == [10, 5, 3]


class TestCorrectionPatternTracker:
    """Tests for CorrectionPatternTracker class."""

    def test_record_pattern_increments_count(self):
        """Recording pattern should increment count."""
        tracker = CorrectionPatternTracker()

        count1 = tracker.record_pattern("teh", "the")
        count2 = tracker.record_pattern("teh", "the")
        count3 = tracker.record_pattern("teh", "the")

        assert count1 == 1
        assert count2 == 2
        assert count3 == 3

    def test_same_word_not_tracked(self):
        """Same word (case-insensitive) should not be tracked."""
        tracker = CorrectionPatternTracker()

        result = tracker.record_pattern("the", "the")
        assert result is None

        result = tracker.record_pattern("The", "the")
        assert result is None

        result = tracker.record_pattern("THE", "the")
        assert result is None

    def test_ignored_pattern_not_tracked(self, tmp_path):
        """Ignored patterns should return None."""
        ignore_path = tmp_path / "ignore.txt"
        ignore_list = IgnoreList(ignore_path=ignore_path)
        ignore_list.add("teh", "the")

        tracker = CorrectionPatternTracker(ignore_list=ignore_list)

        result = tracker.record_pattern("teh", "the")
        assert result is None

    def test_writes_at_threshold(self, tmp_path):
        """Should write to suggestions at threshold."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=3)

        # Record pattern up to threshold
        for i in range(3):
            tracker.record_pattern("teh", "the")

        # Check file was written
        assert sugg_path.exists()
        content = sugg_path.read_text()
        assert "teh=the (corrected 3 times)" in content

    def test_not_written_before_threshold(self, tmp_path):
        """Should not write before threshold is reached."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=5)

        # Record pattern less than threshold
        for i in range(4):
            tracker.record_pattern("teh", "the")

        # File should not exist (nothing written yet)
        assert not sugg_path.exists()

    def test_updates_count_after_threshold(self, tmp_path):
        """Should update count in suggestions after threshold."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=3)

        # Record pattern beyond threshold
        for i in range(5):
            tracker.record_pattern("teh", "the")

        # Check updated count
        content = sugg_path.read_text()
        assert "teh=the (corrected 5 times)" in content

    def test_ignore_removes_from_suggestions(self, tmp_path):
        """Ignoring pattern should remove from suggestions."""
        sugg_path = tmp_path / "suggestions.txt"
        ignore_path = tmp_path / "ignore.txt"

        sf = SuggestionsFile(path=sugg_path)
        ignore_list = IgnoreList(ignore_path=ignore_path)

        tracker = CorrectionPatternTracker(
            ignore_list=ignore_list,
            suggestions_file=sf,
            threshold=3
        )

        # Build up to suggestion
        for i in range(5):
            tracker.record_pattern("teh", "the")

        assert tracker.suggestion_count == 1

        # Now ignore it
        tracker.ignore_pattern("teh", "the")

        assert tracker.suggestion_count == 0
        # Should not be tracked anymore
        result = tracker.record_pattern("teh", "the")
        assert result is None

    def test_get_suggestions(self, tmp_path):
        """Should return current suggestions."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=2)

        for i in range(3):
            tracker.record_pattern("teh", "the")
        for i in range(5):
            tracker.record_pattern("adn", "and")

        suggestions = tracker.get_suggestions()
        assert len(suggestions) == 2
        # Should be sorted by count
        assert suggestions[0][0] == "adn"
        assert suggestions[0][2] == 5
        assert suggestions[1][0] == "teh"
        assert suggestions[1][2] == 3

    def test_threshold_property(self):
        """Should expose threshold property."""
        tracker = CorrectionPatternTracker(threshold=10)
        assert tracker.threshold == 10

    def test_suggestion_count_property(self, tmp_path):
        """Should expose suggestion count property."""
        sugg_path = tmp_path / "suggestions.txt"
        sf = SuggestionsFile(path=sugg_path)

        tracker = CorrectionPatternTracker(suggestions_file=sf, threshold=2)

        assert tracker.suggestion_count == 0

        for i in range(2):
            tracker.record_pattern("teh", "the")

        assert tracker.suggestion_count == 1

    def test_load_method(self, tmp_path):
        """Load should return counts from files."""
        sugg_path = tmp_path / "suggestions.txt"
        ignore_path = tmp_path / "ignore.txt"

        sugg_path.write_text("teh=the (corrected 5 times)\n", encoding="utf-8")
        ignore_path.write_text("adn=and\n", encoding="utf-8")

        sf = SuggestionsFile(path=sugg_path)
        ignore_list = IgnoreList(ignore_path=ignore_path)

        tracker = CorrectionPatternTracker(
            ignore_list=ignore_list,
            suggestions_file=sf
        )

        counts = tracker.load()

        assert counts["suggestions"] == 1
        assert counts["ignored"] == 1

    def test_case_insensitive_tracking(self):
        """Pattern tracking should be case-insensitive."""
        tracker = CorrectionPatternTracker()

        tracker.record_pattern("Teh", "The")
        tracker.record_pattern("TEH", "THE")
        count = tracker.record_pattern("teh", "the")

        # All should count as same pattern
        assert count == 3


class TestSuggestionLinePattern:
    """Tests for the suggestion line regex pattern."""

    def test_parses_standard_format(self):
        """Should parse standard format."""
        match = SUGGESTION_LINE_PATTERN.match("teh=the (corrected 5 times)")
        assert match is not None
        assert match.group(1) == "teh"
        assert match.group(2) == "the"
        assert match.group(3) == "5"

    def test_parses_singular_time(self):
        """Should parse singular 'time'."""
        match = SUGGESTION_LINE_PATTERN.match("teh=the (corrected 1 time)")
        assert match is not None
        assert match.group(3) == "1"

    def test_parses_large_counts(self):
        """Should parse large counts."""
        match = SUGGESTION_LINE_PATTERN.match("teh=the (corrected 999 times)")
        assert match is not None
        assert match.group(3) == "999"

    def test_rejects_invalid_format(self):
        """Should reject invalid formats."""
        assert SUGGESTION_LINE_PATTERN.match("teh=the") is None
        assert SUGGESTION_LINE_PATTERN.match("# comment") is None
        assert SUGGESTION_LINE_PATTERN.match("") is None
