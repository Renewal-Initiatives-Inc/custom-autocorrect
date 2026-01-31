# Phase 3 Execution Plan: Rule Loading & Matching

## Overview

**Goal**: Load correction rules from file and match typed words against them.

**Deliverable**: App that detects when a typed word matches a rule and logs "Would correct X → Y".

**Estimated Complexity**: Medium - File I/O, parsing, and matching logic with file watching

---

## Prerequisites (Phase 2 Verification)

Before starting Phase 3, verify these Phase 2 deliverables are complete:

- [ ] `WordBuffer` class captures characters correctly
- [ ] `KeystrokeEngine` emits completed words on space
- [ ] Backspace and buffer-clear keys work correctly
- [ ] All Phase 2 tests pass (`pytest tests/test_word_buffer.py tests/test_keystroke_engine.py tests/test_properties.py`)
- [ ] Demo prints words when typed in Notepad/Chrome

**Verification Commands**:
```bash
pytest tests/test_word_buffer.py tests/test_keystroke_engine.py tests/test_properties.py -v
python -m custom_autocorrect.main  # Verify words print
```

---

## Requirements Traceability

| Requirement | Criteria | Phase 3 Coverage |
|-------------|----------|------------------|
| REQ-1 | 2. Load rules from rules.txt on startup | ✅ Full |
| REQ-1 | 3. Detect word matches rule + space | ✅ Full |
| REQ-1 | 5. Whole-word matching | ✅ Full |
| REQ-2 | 1. Store rules in Documents/CustomAutocorrect/rules.txt | ✅ Full |
| REQ-2 | 2. Use typo=correction format | ✅ Full |
| REQ-2 | 4. Reload rules when file changes | ✅ Full |
| REQ-2 | 5. Ignore blank lines and # comments | ✅ Full |

**Correctness Properties Validated**:
- CP1: Rule Integrity - For any correction, trigger must exactly match a key in rules.txt
- CP2: Whole-Word Guarantee - Substring matches do NOT trigger corrections

---

## File Structure After Phase 3

```
custom-autocorrect/
├── src/
│   └── custom_autocorrect/
│       ├── __init__.py
│       ├── main.py                 # Modified: integrate RuleMatcher
│       ├── keystroke_engine.py     # Unchanged
│       ├── word_buffer.py          # Unchanged
│       ├── rules.py                # NEW: Rule parsing and matching
│       └── paths.py                # NEW: Application path management
├── tests/
│   ├── test_word_buffer.py
│   ├── test_keystroke_engine.py
│   ├── test_properties.py
│   └── test_rules.py               # NEW: Rule parsing/matching tests
└── Documents/
    └── CustomAutocorrect/
        └── rules.txt               # User's rules file (created at runtime)
```

---

## Task Breakdown

### Task 3.1: Create Path Management Module

**Objective**: Centralize application path handling for the Documents folder structure.

**File**: `src/custom_autocorrect/paths.py`

**Design**:
```python
"""Application path management.

Handles paths for:
- Documents/CustomAutocorrect/ folder structure
- rules.txt, suggestions.txt, etc.
"""

import os
from pathlib import Path
from typing import Optional


def get_app_folder() -> Path:
    """Get the CustomAutocorrect folder in Documents.

    Returns:
        Path to Documents/CustomAutocorrect/
    """
    # On Windows: C:\Users\<user>\Documents\CustomAutocorrect
    # Fallback to app directory if Documents unavailable
    pass


def get_rules_path() -> Path:
    """Get path to rules.txt."""
    return get_app_folder() / "rules.txt"


def ensure_app_folder() -> Path:
    """Create the app folder if it doesn't exist.

    Returns:
        Path to the created/existing folder.
    """
    pass


def ensure_rules_file() -> Path:
    """Create rules.txt with sample content if it doesn't exist.

    Returns:
        Path to the rules file.
    """
    pass
```

**Implementation Notes**:
- Use `os.path.expanduser("~/Documents")` or Windows-specific FOLDERID_Documents
- Handle edge case: Documents folder doesn't exist or isn't writable
- Create folder with appropriate permissions
- Create sample rules.txt with commented examples if missing

**Sample rules.txt content**:
```
# Custom Autocorrect Rules
# Format: typo=correction
# Lines starting with # are comments

# Common typos
teh=the
adn=and
hte=the
```

---

### Task 3.2: Implement Rule Parser

**Objective**: Parse rules.txt into an efficient lookup structure.

**File**: `src/custom_autocorrect/rules.py`

**Class Design**:
```python
"""Rule loading, parsing, and matching.

Correctness Properties:
- CP1: Rule Integrity - corrections only for exact rule matches
- CP2: Whole-Word Guarantee - substring matches do NOT trigger corrections
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Rule:
    """A single correction rule.

    Attributes:
        typo: The misspelled word (stored lowercase for lookup)
        correction: The correct replacement
        original_typo: The typo as it appeared in the file (for debugging)
    """
    typo: str
    correction: str
    original_typo: str


class RuleParseError:
    """Information about a parsing error (not an exception - fail safe)."""
    def __init__(self, line_number: int, line: str, reason: str):
        self.line_number = line_number
        self.line = line
        self.reason = reason


class RuleParser:
    """Parses rules.txt format.

    Format:
        - typo=correction (one per line)
        - Lines starting with # are comments
        - Blank lines are ignored
        - Invalid lines are skipped with a warning
    """

    @staticmethod
    def parse_file(path: Path) -> tuple[Dict[str, Rule], List[RuleParseError]]:
        """Parse a rules file.

        Args:
            path: Path to the rules file.

        Returns:
            Tuple of (rules_dict, parse_errors)
            - rules_dict: Maps lowercase typo to Rule
            - parse_errors: List of errors encountered (for logging)
        """
        pass

    @staticmethod
    def parse_line(line: str) -> Optional[Rule]:
        """Parse a single line into a Rule.

        Args:
            line: A line from rules.txt

        Returns:
            Rule if valid, None if comment/blank/invalid
        """
        pass
```

**Parsing Rules**:
1. Strip whitespace from each line
2. Skip empty lines
3. Skip lines starting with `#`
4. Split on first `=` only (allow `=` in correction, e.g., `eq=equals`)
5. Both typo and correction must be non-empty after stripping
6. Typo must not equal correction (useless rule)
7. Store typo in lowercase for case-insensitive lookup

**Test Cases**:
- Valid: `teh=the`, `EQ=equals`, `a=an`
- Comment: `# this is a comment`, `#comment`
- Blank: ``, `   `, `\t`
- Invalid: `invalid`, `=notypo`, `nocorrection=`, `same=same`
- Edge: `with=equals=sign` → typo="with", correction="equals=sign"

---

### Task 3.3: Implement Rule Matcher

**Objective**: Match completed words against loaded rules.

**Add to `src/custom_autocorrect/rules.py`**:

```python
class RuleMatcher:
    """Matches typed words against correction rules.

    Implements:
    - CP1: Rule Integrity (exact match only)
    - CP2: Whole-Word Guarantee (already satisfied by KeystrokeEngine word extraction)

    Thread Safety: Not thread-safe. Reload should only happen from main thread.
    """

    def __init__(self, rules_path: Optional[Path] = None):
        """Initialize with optional path to rules file.

        Args:
            rules_path: Path to rules.txt. If None, uses default location.
        """
        self._rules: Dict[str, Rule] = {}
        self._rules_path = rules_path
        self._parse_errors: List[RuleParseError] = []
        self._last_modified: float = 0.0

    def load(self) -> int:
        """Load rules from the rules file.

        Returns:
            Number of rules loaded.
        """
        pass

    def match(self, word: str) -> Optional[Rule]:
        """Check if a word matches a correction rule.

        Case-insensitive matching: "TEH" matches rule for "teh".

        Args:
            word: The word to check (from KeystrokeEngine).

        Returns:
            The matching Rule if found, None otherwise.
        """
        pass

    def get_parse_errors(self) -> List[RuleParseError]:
        """Get any parse errors from the last load."""
        return self._parse_errors.copy()

    @property
    def rule_count(self) -> int:
        """Number of active rules."""
        return len(self._rules)

    def has_rule_for(self, typo: str) -> bool:
        """Check if a rule exists for the given typo."""
        return typo.lower() in self._rules
```

**Implementation Notes**:
- Store rules in dict with lowercase typo as key
- `match()` converts input to lowercase before lookup
- Return the full `Rule` object (contains original casing info for Phase 4)

---

### Task 3.4: Implement File Watcher

**Objective**: Automatically reload rules when rules.txt changes.

**Add to `src/custom_autocorrect/rules.py`**:

```python
import threading
import time


class RuleFileWatcher:
    """Watches rules.txt for changes and triggers reload.

    Uses polling rather than OS file notifications for simplicity
    and cross-platform compatibility.

    Poll interval: 2 seconds (balance between responsiveness and CPU usage)
    """

    def __init__(self, matcher: RuleMatcher, poll_interval: float = 2.0):
        """Initialize the watcher.

        Args:
            matcher: The RuleMatcher to reload when file changes.
            poll_interval: Seconds between file checks.
        """
        self._matcher = matcher
        self._poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start watching for file changes."""
        pass

    def stop(self) -> None:
        """Stop watching."""
        pass

    def _watch_loop(self) -> None:
        """Background thread that polls for file changes."""
        pass
```

**Implementation Notes**:
- Compare file modification time (mtime) each poll
- If mtime changed, call `matcher.load()`
- Handle file not found (file deleted temporarily)
- Handle file locked (being edited)
- Log reload events at INFO level
- Daemon thread so it doesn't prevent clean shutdown

**Alternative**: For Phase 3, simple polling is sufficient. Could use `watchdog` library later if polling proves insufficient.

---

### Task 3.5: Integrate with KeystrokeEngine

**Objective**: Connect rule matching to word detection.

**Modify**: `src/custom_autocorrect/main.py`

**Integration Pattern**:
```python
from .rules import RuleMatcher, RuleFileWatcher
from .paths import ensure_app_folder, get_rules_path, ensure_rules_file


def on_word_detected(word: str, matcher: RuleMatcher) -> None:
    """Check typed word against rules and log potential corrections.

    Phase 3: Logs "Would correct X → Y"
    Phase 4: Will actually perform the correction
    """
    rule = matcher.match(word)
    if rule:
        # Phase 3: Just log (no actual correction yet)
        print(f"Would correct: '{word}' → '{rule.correction}'")
        logger.info(f"Match found: '{word}' → '{rule.correction}' (rule: {rule.original_typo})")
    else:
        # Debug: show word was processed but no match
        logger.debug(f"No rule match for: '{word}'")


def main() -> int:
    # ... existing setup ...

    # Phase 3: Set up rule matching
    ensure_app_folder()
    ensure_rules_file()

    matcher = RuleMatcher()
    rule_count = matcher.load()
    print(f"Loaded {rule_count} correction rules from {matcher._rules_path}")

    # Report any parse errors
    for error in matcher.get_parse_errors():
        print(f"Warning: Line {error.line_number}: {error.reason}")

    # Start file watcher
    watcher = RuleFileWatcher(matcher)
    watcher.start()

    # Create callback with matcher bound
    def word_callback(word: str) -> None:
        on_word_detected(word, matcher)

    engine = KeystrokeEngine(on_word_complete=word_callback)

    try:
        engine.start()
        # ... existing event loop ...
    finally:
        watcher.stop()
        engine.stop()
```

---

### Task 3.6: Write Unit Tests for Rule Parsing

**File**: `tests/test_rules.py` (replace placeholder)

**Test Cases**:

```python
import pytest
from pathlib import Path
import tempfile

from custom_autocorrect.rules import Rule, RuleParser, RuleMatcher


class TestRuleDataclass:
    """Tests for the Rule dataclass."""

    def test_rule_creation(self):
        """Rule stores typo, correction, and original."""
        rule = Rule(typo="teh", correction="the", original_typo="teh")
        assert rule.typo == "teh"
        assert rule.correction == "the"

    def test_rule_is_hashable(self):
        """Rule can be used in sets (frozen=True)."""
        rule = Rule(typo="teh", correction="the", original_typo="teh")
        rules_set = {rule}
        assert rule in rules_set


class TestRuleParser:
    """Tests for parsing rules.txt format."""

    def test_parse_valid_rule(self):
        """Parse a valid typo=correction line."""
        rule = RuleParser.parse_line("teh=the")
        assert rule is not None
        assert rule.typo == "teh"
        assert rule.correction == "the"

    def test_parse_with_whitespace(self):
        """Whitespace around = is handled."""
        rule = RuleParser.parse_line("  teh = the  ")
        assert rule is not None
        assert rule.typo == "teh"
        assert rule.correction == "the"

    def test_parse_comment_line(self):
        """Lines starting with # return None."""
        assert RuleParser.parse_line("# this is a comment") is None
        assert RuleParser.parse_line("#comment") is None

    def test_parse_blank_line(self):
        """Blank lines return None."""
        assert RuleParser.parse_line("") is None
        assert RuleParser.parse_line("   ") is None
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

    def test_parse_equals_in_correction(self):
        """Equals sign allowed in correction."""
        rule = RuleParser.parse_line("eq=a=b")
        assert rule is not None
        assert rule.typo == "eq"
        assert rule.correction == "a=b"

    def test_parse_preserves_original_typo(self):
        """Original typo casing is preserved."""
        rule = RuleParser.parse_line("TEH=the")
        assert rule.original_typo == "TEH"
        assert rule.typo == "teh"  # Lowercase for lookup


class TestRuleParserFile:
    """Tests for parsing complete files."""

    def test_parse_file_with_rules(self, tmp_path):
        """Parse a file with multiple rules."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\nadn=and\n")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 2
        assert "teh" in rules
        assert "adn" in rules
        assert len(errors) == 0

    def test_parse_file_with_comments(self, tmp_path):
        """Comments are ignored."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("# Header\nteh=the\n# Footer\n")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 1
        assert "teh" in rules

    def test_parse_file_missing(self, tmp_path):
        """Missing file returns empty rules."""
        rules_file = tmp_path / "nonexistent.txt"

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 0

    def test_parse_file_reports_errors(self, tmp_path):
        """Invalid lines reported in errors list."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\ninvalid\nadn=and\n")

        rules, errors = RuleParser.parse_file(rules_file)

        assert len(rules) == 2
        assert len(errors) == 1
        assert errors[0].line_number == 2


class TestRuleMatcher:
    """Tests for matching words against rules."""

    @pytest.fixture
    def matcher_with_rules(self, tmp_path):
        """Create a matcher with sample rules."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("teh=the\nadn=and\nHTE=the\n")
        matcher = RuleMatcher(rules_path=rules_file)
        matcher.load()
        return matcher

    def test_match_exact(self, matcher_with_rules):
        """Exact lowercase match returns rule."""
        rule = matcher_with_rules.match("teh")
        assert rule is not None
        assert rule.correction == "the"

    def test_match_case_insensitive(self, matcher_with_rules):
        """Match is case-insensitive."""
        assert matcher_with_rules.match("TEH") is not None
        assert matcher_with_rules.match("Teh") is not None
        assert matcher_with_rules.match("tEh") is not None

    def test_no_match_returns_none(self, matcher_with_rules):
        """Unknown word returns None."""
        assert matcher_with_rules.match("hello") is None
        assert matcher_with_rules.match("the") is None  # Correction, not typo

    def test_rule_count(self, matcher_with_rules):
        """Rule count reflects loaded rules."""
        assert matcher_with_rules.rule_count == 3

    def test_has_rule_for(self, matcher_with_rules):
        """Check if rule exists."""
        assert matcher_with_rules.has_rule_for("teh")
        assert matcher_with_rules.has_rule_for("TEH")  # Case insensitive
        assert not matcher_with_rules.has_rule_for("hello")

    def test_load_returns_count(self, tmp_path):
        """Load returns number of rules loaded."""
        rules_file = tmp_path / "rules.txt"
        rules_file.write_text("a=b\nc=d\ne=f\n")

        matcher = RuleMatcher(rules_path=rules_file)
        count = matcher.load()

        assert count == 3
```

---

### Task 3.7: Write Property-Based Tests for Rule Integrity (CP1)

**Add to**: `tests/test_properties.py`

```python
from custom_autocorrect.rules import Rule, RuleParser, RuleMatcher


class TestRuleIntegrityProperty:
    """Property-based tests for CP1: Rule Integrity.

    For any correction that occurs, the trigger must exactly match
    a key in rules.txt (case-insensitive matching).
    """

    # Strategy for generating valid rule typos (no =, no #)
    rule_typo = st.text(
        alphabet=st.characters(
            whitelist_categories=["Lu", "Ll", "Nd"],
            min_codepoint=32,
            max_codepoint=126,
        ),
        min_size=1,
        max_size=20,
    ).filter(lambda s: "=" not in s and not s.startswith("#") and s.strip())

    # Strategy for generating valid corrections
    rule_correction = st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=1,
        max_size=50,
    ).filter(lambda s: s.strip())

    @given(rule_typo, rule_correction)
    def test_match_only_if_rule_exists(self, typo: str, correction: str):
        """Matcher only returns rule if it was loaded."""
        assume(typo.lower() != correction.lower())  # Valid rule

        matcher = RuleMatcher()
        # Don't load any rules

        # Should not match anything
        assert matcher.match(typo) is None

    @given(rule_typo, rule_correction)
    def test_match_returns_exact_loaded_rule(self, typo: str, correction: str):
        """Match returns the exact rule that was loaded."""
        assume(typo.lower() != correction.lower())

        # Create temporary rules file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
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
    def test_all_loaded_rules_match(self, rules: list):
        """All loaded rules should be matchable."""
        # Filter to valid rules (typo != correction)
        valid_rules = [(t, c) for t, c in rules if t.lower() != c.lower()]
        assume(len(valid_rules) > 0)

        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
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
```

---

### Task 3.8: Manual Integration Testing

**Objective**: Verify rule matching works end-to-end.

**Test Procedure**:

1. **Set up rules file**:
   ```
   # Test rules for Phase 3
   teh=the
   adn=and
   hte=the
   ```
   Save to `Documents/CustomAutocorrect/rules.txt`

2. **Run the app**:
   ```bash
   python -m custom_autocorrect.main
   ```

3. **Test in Notepad**:
   - Type "teh " (with space)
   - Console should show: `Would correct: 'teh' → 'the'`
   - Type "hello " (no rule)
   - Console should show: `Word detected: 'hello'` (or no output if only logging matches)

4. **Test case insensitivity**:
   - Type "TEH "
   - Should match the "teh" rule

5. **Test file hot-reload**:
   - While app running, edit rules.txt
   - Add: `thsi=this`
   - Wait 2-3 seconds (file watcher poll interval)
   - Console should log: "Rules reloaded: 4 rules"
   - Type "thsi "
   - Should show: `Would correct: 'thsi' → 'this'`

6. **Test with invalid rules**:
   - Add invalid line to rules.txt: `invalidline`
   - Verify app logs warning but continues working
   - Other rules still function

**Expected Results Checklist**:
- [ ] Rules loaded on startup (count displayed)
- [ ] Matching words show "Would correct" message
- [ ] Non-matching words don't trigger correction message
- [ ] Case variations all match (teh, Teh, TEH)
- [ ] File changes trigger reload
- [ ] Invalid rules logged but don't break app
- [ ] App folder created if missing
- [ ] Sample rules.txt created if missing

---

## Acceptance Criteria Mapping

| Acceptance Criteria | Test/Verification |
|--------------------|-------------------|
| Rules loaded from rules.txt on startup | `test_load_returns_count`, manual verification |
| typo=correction format parsed | `TestRuleParser` test class |
| Comments (#) ignored | `test_parse_comment_line` |
| Blank lines ignored | `test_parse_blank_line` |
| Case-insensitive matching | `test_match_case_insensitive` |
| File changes trigger reload | Manual test with file watcher |
| Parse errors don't crash app | `test_parse_file_reports_errors` |

---

## Definition of Done

Phase 3 is complete when:

- [ ] `paths.py` creates Documents/CustomAutocorrect/ folder structure
- [ ] `rules.py` parses rules.txt (typo=correction format)
- [ ] Comments and blank lines are handled correctly
- [ ] Case-insensitive rule lookup works
- [ ] RuleFileWatcher reloads rules on file change
- [ ] main.py integrates rule matching with keystroke engine
- [ ] "Would correct X → Y" logged when match found
- [ ] All unit tests pass (`pytest tests/test_rules.py -v`)
- [ ] All property tests pass (`pytest tests/test_properties.py -v`)
- [ ] Manual testing verifies end-to-end flow
- [ ] Parse errors logged but don't crash the app
- [ ] Code committed and pushed to GitHub

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Documents folder doesn't exist | Fall back to app directory; log warning |
| Rules file locked by editor | Retry with backoff; skip reload if persistent |
| Unicode in rules file | Use UTF-8 encoding explicitly |
| Large rules file | Dict lookup is O(1); even 1000 rules is instant |
| File watcher CPU usage | 2-second poll interval is negligible |

---

## Files Created/Modified Summary

| File | Action | Purpose |
|------|--------|---------|
| `src/custom_autocorrect/paths.py` | Create | Application path management |
| `src/custom_autocorrect/rules.py` | Replace | Rule parsing, matching, file watching |
| `src/custom_autocorrect/main.py` | Modify | Integrate rule matching |
| `tests/test_rules.py` | Replace | Rule parsing and matching tests |
| `tests/test_properties.py` | Modify | Add rule integrity property tests |

---

## Next Phase Preview

Phase 4 (Correction Engine) will build on this foundation:
- Replace "Would correct X → Y" logging with actual correction
- Implement backspace × word length, type correction, type space
- Implement casing preservation (lowercase → lowercase, etc.)
- The `Rule` object from `match()` will provide the correction text
