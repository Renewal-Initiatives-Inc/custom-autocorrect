"""Tests for rule parsing and matching.

Phase 3 tests for:
- Valid rule parsing (typo=correction format)
- Comment and blank line handling
- Case-insensitive lookup
- Whole-word matching (implicit via KeystrokeEngine)
- Unicode support
"""

import pytest
import tempfile
import time
from pathlib import Path

from custom_autocorrect.rules import (
    Rule,
    RuleParseError,
    RuleParser,
    RuleMatcher,
    RuleFileWatcher,
)


class TestRuleDataclass:
    """Tests for the Rule dataclass."""

    def test_rule_creation(self):
        """Rule stores typo, correction, and original."""
        rule = Rule(typo="teh", correction="the", original_typo="teh")
        assert rule.typo == "teh"
        assert rule.correction == "the"
        assert rule.original_typo == "teh"

    def test_rule_is_frozen(self):
        """Rule is immutable (frozen=True)."""
        rule = Rule(typo="teh", correction="the", original_typo="teh")
        with pytest.raises(AttributeError):
            rule.typo = "foo"

    def test_rule_is_hashable(self):
        """Rule can be used in sets (frozen=True)."""
        rule = Rule(typo="teh", correction="the", original_typo="teh")
        rules_set = {rule}
        assert rule in rules_set

    def test_rule_equality(self):
        """Two rules with same values are equal."""
        rule1 = Rule(typo="teh", correction="the", original_typo="teh")
        rule2 = Rule(typo="teh", correction="the", original_typo="teh")
        assert rule1 == rule2


class TestRuleParseError:
    """Tests for RuleParseError."""

    def test_error_stores_info(self):
        """Error stores line number, line content, and reason."""
        error = RuleParseError(
            line_number=5,
            line="invalid",
            reason="Missing equals sign",
        )
        assert error.line_number == 5
        assert error.line == "invalid"
        assert error.reason == "Missing equals sign"


class TestRuleParserParseLine:
    """Tests for RuleParser.parse_line()."""

    def test_parse_valid_rule(self):
        """Parse a valid typo=correction line."""
        rule = RuleParser.parse_line("teh=the")
        assert rule is not None
        assert rule.typo == "teh"
        assert rule.correction == "the"

    def test_parse_stores_lowercase_typo(self):
        """Typo is stored lowercase for lookup."""
        rule = RuleParser.parse_line("TEH=the")
        assert rule is not None
        assert rule.typo == "teh"
        assert rule.original_typo == "TEH"

    def test_parse_with_whitespace(self):
        """Whitespace around = is handled."""
        rule = RuleParser.parse_line("  teh = the  ")
        assert rule is not None
        assert rule.typo == "teh"
        assert rule.correction == "the"

    def test_parse_comment_line_hash(self):
        """Lines starting with # return None."""
        assert RuleParser.parse_line("# this is a comment") is None

    def test_parse_comment_line_hash_no_space(self):
        """Comment without space after #."""
        assert RuleParser.parse_line("#comment") is None

    def test_parse_blank_line_empty(self):
        """Empty string returns None."""
        assert RuleParser.parse_line("") is None

    def test_parse_blank_line_spaces(self):
        """Spaces-only returns None."""
        assert RuleParser.parse_line("   ") is None

    def test_parse_blank_line_tab(self):
        """Tab-only returns None."""
        assert RuleParser.parse_line("\t") is None

    def test_parse_no_equals(self):
        """Lines without = return None."""
        assert RuleParser.parse_line("invalid") is None

    def test_parse_empty_typo(self):
        """Empty typo returns None."""
        assert RuleParser.parse_line("=correction") is None

    def test_parse_empty_correction(self):
        """Empty correction returns None."""
        assert RuleParser.parse_line("typo=") is None

    def test_parse_same_typo_correction(self):
        """Typo same as correction returns None."""
        assert RuleParser.parse_line("same=same") is None

    def test_parse_same_typo_correction_case_insensitive(self):
        """Typo same as correction (different case) returns None."""
        assert RuleParser.parse_line("Same=SAME") is None

    def test_parse_equals_in_correction(self):
        """Equals sign allowed in correction."""
        rule = RuleParser.parse_line("eq=a=b")
        assert rule is not None
        assert rule.typo == "eq"
        assert rule.correction == "a=b"

    def test_parse_preserves_correction_case(self):
        """Correction preserves original casing."""
        rule = RuleParser.parse_line("teh=The")
        assert rule.correction == "The"

    def test_parse_unicode_typo(self):
        """Unicode characters in typo."""
        rule = RuleParser.parse_line("cafe=caf\u00e9")
        assert rule is not None
        assert rule.typo == "cafe"
        assert rule.correction == "caf\u00e9"

    def test_parse_unicode_correction(self):
        """Unicode characters in correction."""
        rule = RuleParser.parse_line("naive=na\u00efve")
        assert rule is not None
        assert rule.correction == "na\u00efve"


class TestRuleParserParseFile:
    """Tests for RuleParser.parse_file()."""

    def test_parse_file_with_rules(self, tmp_path):
        """Parse a file with multiple rules."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\nadn=and\n", encoding="utf-8")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 2
        assert "teh" in rules
        assert "adn" in rules
        assert len(errors) == 0

    def test_parse_file_with_comments(self, tmp_path):
        """Comments are ignored."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text(
            "# Header\nteh=the\n# Footer\n", encoding="utf-8"
        )

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 1
        assert "teh" in rules
        assert len(errors) == 0

    def test_parse_file_with_blank_lines(self, tmp_path):
        """Blank lines are ignored."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text(
            "teh=the\n\n\nadn=and\n   \n", encoding="utf-8"
        )

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 2

    def test_parse_file_missing(self, tmp_path):
        """Missing file returns empty rules."""
        rules_file = tmp_path / "nonexistent.txt"

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 0
        assert len(errors) == 0

    def test_parse_file_reports_errors(self, tmp_path):
        """Invalid lines reported in errors list."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\ninvalid\nadn=and\n", encoding="utf-8")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 2
        assert len(errors) == 1
        assert errors[0].line_number == 2
        assert errors[0].line == "invalid"

    def test_parse_file_multiple_errors(self, tmp_path):
        """Multiple invalid lines all reported."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("bad1\nbad2\nteh=the\nbad3\n", encoding="utf-8")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 1
        assert len(errors) == 3
        assert [e.line_number for e in errors] == [1, 2, 4]

    def test_parse_file_duplicate_typos(self, tmp_path):
        """Duplicate typos use the latest definition."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\nteh=that\n", encoding="utf-8")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 1
        assert rules["teh"].correction == "that"

    def test_parse_file_utf8(self, tmp_path):
        """File with UTF-8 encoding."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("cafe=caf\u00e9\n", encoding="utf-8")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 1
        assert rules["cafe"].correction == "caf\u00e9"


class TestRuleMatcher:
    """Tests for RuleMatcher."""

    @pytest.fixture
    def matcher_with_rules(self, tmp_path):
        """Create a matcher with sample rules."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\nadn=and\nhte=the\n", encoding="utf-8")
        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()
        return matcher

    def test_match_exact_lowercase(self, matcher_with_rules):
        """Exact lowercase match returns rule."""
        rule = matcher_with_rules.match("teh")
        assert rule is not None
        assert rule.correction == "the"

    def test_match_case_insensitive_upper(self, matcher_with_rules):
        """Uppercase input matches lowercase rule."""
        rule = matcher_with_rules.match("TEH")
        assert rule is not None
        assert rule.correction == "the"

    def test_match_case_insensitive_title(self, matcher_with_rules):
        """Title case input matches lowercase rule."""
        rule = matcher_with_rules.match("Teh")
        assert rule is not None
        assert rule.correction == "the"

    def test_match_case_insensitive_mixed(self, matcher_with_rules):
        """Mixed case input matches lowercase rule."""
        rule = matcher_with_rules.match("tEh")
        assert rule is not None

    def test_no_match_returns_none(self, matcher_with_rules):
        """Unknown word returns None."""
        assert matcher_with_rules.match("hello") is None

    def test_no_match_for_correction(self, matcher_with_rules):
        """Correction word itself doesn't match."""
        # "the" is a correction, not a typo
        assert matcher_with_rules.match("the") is None

    def test_rule_count(self, matcher_with_rules):
        """Rule count reflects loaded rules."""
        assert matcher_with_rules.rule_count == 3

    def test_has_rule_for_exists(self, matcher_with_rules):
        """has_rule_for returns True for existing rule."""
        assert matcher_with_rules.has_rule_for("teh")

    def test_has_rule_for_case_insensitive(self, matcher_with_rules):
        """has_rule_for is case insensitive."""
        assert matcher_with_rules.has_rule_for("TEH")
        assert matcher_with_rules.has_rule_for("Teh")

    def test_has_rule_for_not_exists(self, matcher_with_rules):
        """has_rule_for returns False for missing rule."""
        assert not matcher_with_rules.has_rule_for("hello")

    def test_load_returns_count(self, tmp_path):
        """Load returns number of rules loaded."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("a=b\nc=d\ne=f\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        count = matcher.load()

        assert count == 3

    def test_load_empty_file(self, tmp_path):
        """Load empty file returns 0."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        count = matcher.load()

        assert count == 0
        assert matcher.rule_count == 0

    def test_get_parse_errors(self, tmp_path):
        """Parse errors are accessible."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("valid=rule\ninvalid\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()

        errors = matcher.get_parse_errors()
        assert len(errors) == 1
        assert errors[0].line == "invalid"

    def test_get_all_rules(self, matcher_with_rules):
        """get_all_rules returns all loaded rules."""
        rules = matcher_with_rules.get_all_rules()
        assert len(rules) == 3
        typos = {r.typo for r in rules}
        assert typos == {"teh", "adn", "hte"}

    def test_reload_if_changed_detects_change(self, tmp_path):
        """reload_if_changed detects file modifications."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()
        assert matcher.rule_count == 1

        # Modify file
        time.sleep(0.1)  # Ensure different mtime
        rules_file.write_text("teh=the\nadn=and\n", encoding="utf-8")

        reloaded = matcher.reload_if_changed()
        assert reloaded is True
        assert matcher.rule_count == 2

    def test_reload_if_changed_no_change(self, tmp_path):
        """reload_if_changed returns False when unchanged."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()

        reloaded = matcher.reload_if_changed()
        assert reloaded is False


class TestRuleFileWatcher:
    """Tests for RuleFileWatcher."""

    def test_watcher_starts_and_stops(self, tmp_path):
        """Watcher can start and stop."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()

        watcher = RuleFileWatcher(matcher, poll_interval=0.1)

        assert not watcher.is_running
        watcher.start()
        assert watcher.is_running
        watcher.stop()
        assert not watcher.is_running

    def test_watcher_start_twice_is_safe(self, tmp_path):
        """Starting watcher twice doesn't create duplicate threads."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        watcher = RuleFileWatcher(matcher, poll_interval=0.1)

        watcher.start()
        watcher.start()  # Should be a no-op
        assert watcher.is_running
        watcher.stop()

    def test_watcher_stop_when_not_running(self, tmp_path):
        """Stopping non-running watcher is safe."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        watcher = RuleFileWatcher(matcher, poll_interval=0.1)

        watcher.stop()  # Should not raise
        assert not watcher.is_running

    def test_watcher_detects_changes(self, tmp_path):
        """Watcher reloads rules when file changes."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\n", encoding="utf-8")

        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()
        assert matcher.rule_count == 1

        watcher = RuleFileWatcher(matcher, poll_interval=0.1)
        watcher.start()

        try:
            # Modify file
            time.sleep(0.15)  # Give watcher time to check
            rules_file.write_text("teh=the\nadn=and\n", encoding="utf-8")
            time.sleep(0.25)  # Wait for watcher to detect change

            # Rules should be reloaded
            assert matcher.rule_count == 2
        finally:
            watcher.stop()


class TestRuleMatcherIntegration:
    """Integration tests for rule matching flow."""

    def test_full_parsing_and_matching_flow(self, tmp_path):
        """Test complete flow from file to match."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text(
            "# My correction rules\n"
            "\n"
            "teh=the\n"
            "adn=and\n"
            "hte=the\n"
            "\n"
            "# More rules\n"
            "taht=that\n",
            encoding="utf-8",
        )

        matcher = RuleMatcher(rules_path=rules_file)
        count = matcher.load()

        assert count == 4
        assert len(matcher.get_parse_errors()) == 0

        # Test matching
        assert matcher.match("teh").correction == "the"
        assert matcher.match("TEH").correction == "the"
        assert matcher.match("adn").correction == "and"
        assert matcher.match("hello") is None
