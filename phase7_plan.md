# Phase 7: Pattern Suggestion System - Execution Plan

## Overview

**Goal**: Detect typo patterns from user behavior (backspace corrections) and log suggestions.

**Key Principle**: Never auto-create rules. The system detects patterns from backspace corrections and writes them to suggestions.txt for user review.

**Approach Change**: Instead of a dictionary-based approach (checking every word against 10K+ words), we use **backspace detection** - when a user types a word, deletes it, and types a different word, that's a direct signal of a correction pattern they care about.

**Requirements Addressed**:
- REQ-4: Pattern Suggestion (revised approach)
- REQ-5: Ignore List Management (partial - file support only; UI in Phase 8)

**Correctness Property**:
- CP4 (Revised): For any pattern appearing in suggestions.txt, that pattern must represent a word the user typed, deleted via backspace, and replaced with a different word, at least 5 times.

---

## Why Backspace Detection (Not Dictionary)

| Aspect | Dictionary Approach | Backspace Approach |
|--------|--------------------|--------------------|
| **Compute** | Check every word against 10K+ dictionary | Just track backspace sequences |
| **False positives** | Many (names, jargon, acronyms) | Very few (only actual corrections) |
| **Files needed** | dictionary + custom-words + ignore + suggestions | Just suggestions + ignore |
| **Signal quality** | Indirect (not in dictionary) | Direct (user chose to fix it) |
| **Setup** | Bundle 10K word file | Nothing to bundle |
| **Alignment** | Over-engineered for 10-50 typos | Perfect for 10-50 typos |

---

## How It Works

### Detection Flow

```
1. User types "teh"
2. Buffer contains: ['t', 'e', 'h']
3. User presses backspace 3x (deletes entire word)
4. System saves "teh" as "erased_word"
5. User types "the"
6. User presses space
7. System detects: erased_word="teh", new_word="the"
8. System records correction pattern: teh → the
9. After 5 occurrences, writes to suggestions.txt:
   teh=the (corrected 5 times)
```

### Edge Cases

- **Partial backspace**: User types "tehh", backspaces once, types "e" → "tehe" not "teh→the"
- **Multiple words erased**: Only track the immediately preceding erased word
- **Same word retyped**: "teh" → backspace → "teh" = not a correction (words are same)
- **Buffer clear keys**: Enter/Tab/Escape clear both buffer and erased_word tracking

---

## Dependencies Check

Before starting Phase 7, verify these deliverables are working:

- [ ] `keystroke_engine.py` handles backspace correctly (removes last char from buffer)
- [ ] `paths.py` provides `get_suggestions_path()` and `get_ignore_path()`
- [ ] Test infrastructure (pytest, hypothesis) is working
- [ ] App folder creation (`ensure_app_folder()`) works

---

## Task Breakdown

### Task 1: Extend WordBuffer to Track Erased Words

**Goal**: When backspace clears the entire buffer, save what was erased.

**Files to modify**:
- `src/custom_autocorrect/word_buffer.py`

**Changes needed**:

```python
class WordBuffer:
    def __init__(self):
        self._chars: list[str] = []
        self._erased_word: str = ""  # NEW: last word that was fully erased

    def remove_last(self) -> str:
        """Remove and return the last character, or empty string if empty."""
        if self._chars:
            char = self._chars.pop()
            # If buffer is now empty, we just erased a complete word
            if not self._chars and self._erased_word == "":
                # Don't overwrite if we're still backspacing through same erasure
                pass
            return char
        return ""

    def get_erased_word(self) -> str:
        """Get the word that was erased (if any)."""
        return self._erased_word

    def clear_erased_word(self) -> None:
        """Clear the erased word tracking."""
        self._erased_word = ""

    def _save_as_erased(self) -> None:
        """Save current buffer as erased word before clearing."""
        if self._chars:
            self._erased_word = self.get_word()
```

**Implementation detail**: The tricky part is detecting "word fully erased by backspace" vs "buffer cleared by Enter/Tab". We need to track this in KeystrokeEngine.

**Acceptance criteria**:
- [ ] When backspaces erase entire word, it's saved as erased_word
- [ ] When clear keys (Enter/Tab/Escape) clear buffer, erased_word is also cleared
- [ ] get_erased_word() returns the last erased word

---

### Task 2: Modify KeystrokeEngine to Detect Correction Patterns

**Goal**: When a word is completed, check if it replaced an erased word.

**Files to modify**:
- `src/custom_autocorrect/keystroke_engine.py`

**Changes needed**:

Add a new callback for correction patterns:

```python
class KeystrokeEngine:
    def __init__(
        self,
        on_word_complete: Optional[Callable[[str], None]] = None,
        on_correction_pattern: Optional[Callable[[str, str], None]] = None,  # NEW
    ):
        self.buffer = WordBuffer()
        self._on_word_complete = on_word_complete
        self._on_correction_pattern = on_correction_pattern  # NEW
        self._erased_word: str = ""  # Track word erased by backspaces

    def _handle_backspace(self) -> None:
        """Handle backspace key."""
        # Before removing, check if this will empty the buffer
        if len(self.buffer) == 1:
            # This backspace will empty the buffer - save what's being erased
            self._erased_word = self.buffer.get_word()

        self.buffer.remove_last()

    def _handle_space(self) -> None:
        """Handle space key - word boundary."""
        word = self.buffer.get_word()
        self.buffer.clear()

        if word:
            # Check for correction pattern BEFORE calling on_word_complete
            if self._erased_word and self._erased_word.lower() != word.lower():
                if self._on_correction_pattern:
                    self._on_correction_pattern(self._erased_word, word)

            # Clear erased word tracking
            self._erased_word = ""

            # Normal word completion callback
            if self._on_word_complete:
                self._on_word_complete(word)

    def _handle_clear_key(self) -> None:
        """Handle keys that clear the buffer (Enter, Tab, Escape, arrows)."""
        self.buffer.clear()
        self._erased_word = ""  # Also clear erased word tracking
```

**Acceptance criteria**:
- [ ] Detects when word is erased by backspace then replaced
- [ ] Calls on_correction_pattern(erased, replacement) callback
- [ ] Ignores if erased == replacement (case-insensitive)
- [ ] Clears tracking on clear keys (Enter/Tab/Escape/arrows)

---

### Task 3: Implement CorrectionPatternTracker

**Goal**: Track correction patterns and write to suggestions.txt at threshold.

**Files to modify**:
- `src/custom_autocorrect/suggestions.py`

**Implementation**:

```python
"""Pattern suggestion system using backspace detection.

Phase 7 Implementation:
- Tracks correction patterns (erased_word → new_word)
- Writes patterns to suggestions.txt after threshold reached
- Supports ignore.txt for patterns to skip
"""

import logging
import re
from collections import Counter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Constants
SUGGESTION_THRESHOLD = 5

# File format pattern for parsing suggestions.txt
SUGGESTION_LINE_PATTERN = re.compile(r"^(.+?)=(.+?)\s+\(corrected\s+(\d+)\s+times?\)$")


class IgnoreList:
    """Manages patterns to never suggest."""

    def __init__(self, ignore_path: Optional[Path] = None):
        self._ignored: set[str] = set()  # Store as "typo=correction" keys
        self._path = ignore_path

    def load(self) -> int:
        """Load ignored patterns from file."""
        self._ignored.clear()

        if not self._path or not self._path.exists():
            return 0

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().lower()
                    if line and not line.startswith("#"):
                        self._ignored.add(line)
        except OSError as e:
            logger.warning(f"Failed to load ignore list: {e}")

        return len(self._ignored)

    def is_ignored(self, typo: str, correction: str) -> bool:
        """Check if pattern should be ignored."""
        key = f"{typo.lower()}={correction.lower()}"
        return key in self._ignored

    def add(self, typo: str, correction: str) -> bool:
        """Add pattern to ignore list."""
        key = f"{typo.lower()}={correction.lower()}"
        if key in self._ignored:
            return True

        self._ignored.add(key)

        if self._path:
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(f"{key}\n")
                return True
            except OSError as e:
                logger.warning(f"Failed to save ignored pattern: {e}")
                return False
        return True

    def __len__(self) -> int:
        return len(self._ignored)


class SuggestionsFile:
    """Manages suggestions.txt file operations."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path
        self._suggestions: dict[str, tuple[str, int]] = {}  # key -> (correction, count)

    def _make_key(self, typo: str, correction: str) -> str:
        return f"{typo.lower()}={correction.lower()}"

    def load(self) -> int:
        """Load existing suggestions from file."""
        self._suggestions.clear()

        if not self._path or not self._path.exists():
            return 0

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    match = SUGGESTION_LINE_PATTERN.match(line)
                    if match:
                        typo = match.group(1).lower()
                        correction = match.group(2).lower()
                        count = int(match.group(3))
                        key = self._make_key(typo, correction)
                        self._suggestions[key] = (correction, count)
        except OSError as e:
            logger.warning(f"Failed to load suggestions: {e}")

        return len(self._suggestions)

    def add_or_update(self, typo: str, correction: str, count: int) -> bool:
        """Add or update a suggestion."""
        key = self._make_key(typo, correction)
        self._suggestions[key] = (correction.lower(), count)
        return self._save()

    def remove(self, typo: str, correction: str) -> bool:
        """Remove a pattern from suggestions."""
        key = self._make_key(typo, correction)
        if key in self._suggestions:
            del self._suggestions[key]
            return self._save()
        return True

    def _save(self) -> bool:
        """Save all suggestions to file."""
        if not self._path:
            return False

        try:
            with open(self._path, "w", encoding="utf-8") as f:
                f.write("# Suggested Corrections\n")
                f.write("# Detected from your typing patterns (backspace corrections)\n")
                f.write("# To enable: copy the line to rules.txt (remove the count part)\n")
                f.write("# To ignore: add to ignore.txt\n")
                f.write("#\n")

                # Sort by count descending
                sorted_suggestions = sorted(
                    self._suggestions.items(),
                    key=lambda x: -x[1][1]  # Sort by count descending
                )

                for key, (correction, count) in sorted_suggestions:
                    typo = key.split("=")[0]
                    f.write(f"{typo}={correction} (corrected {count} times)\n")

            return True
        except OSError as e:
            logger.warning(f"Failed to save suggestions: {e}")
            return False

    def get_all(self) -> list[tuple[str, str, int]]:
        """Get all suggestions as (typo, correction, count) tuples."""
        result = []
        for key, (correction, count) in self._suggestions.items():
            typo = key.split("=")[0]
            result.append((typo, correction, count))
        return result

    def __len__(self) -> int:
        return len(self._suggestions)


class CorrectionPatternTracker:
    """Tracks correction patterns and manages suggestions.

    This is the primary interface used by main.py to track patterns
    detected from backspace corrections.
    """

    def __init__(
        self,
        ignore_list: Optional[IgnoreList] = None,
        suggestions_file: Optional[SuggestionsFile] = None,
        threshold: int = SUGGESTION_THRESHOLD,
    ):
        self._ignore_list = ignore_list
        self._suggestions_file = suggestions_file
        self._threshold = threshold
        self._counts: Counter = Counter()  # "typo=correction" -> count

    @classmethod
    def create_default(cls) -> "CorrectionPatternTracker":
        """Create tracker with default paths."""
        from .paths import get_suggestions_path, get_ignore_path

        ignore_list = IgnoreList(ignore_path=get_ignore_path())
        suggestions_file = SuggestionsFile(path=get_suggestions_path())

        return cls(
            ignore_list=ignore_list,
            suggestions_file=suggestions_file,
        )

    def load(self) -> dict[str, int]:
        """Load all data files."""
        counts = {}

        if self._ignore_list:
            counts["ignored"] = self._ignore_list.load()

        if self._suggestions_file:
            counts["suggestions"] = self._suggestions_file.load()

        return counts

    def record_pattern(self, erased: str, replacement: str) -> Optional[int]:
        """Record a correction pattern.

        Called when user erases a word and types a different one.

        Args:
            erased: The word that was erased.
            replacement: The word typed to replace it.

        Returns:
            Current count if pattern is being tracked, None if ignored.
        """
        erased_lower = erased.lower()
        replacement_lower = replacement.lower()

        # Skip if same word (not a correction)
        if erased_lower == replacement_lower:
            return None

        # Skip if ignored
        if self._ignore_list and self._ignore_list.is_ignored(erased_lower, replacement_lower):
            return None

        # Track frequency
        key = f"{erased_lower}={replacement_lower}"
        self._counts[key] += 1
        count = self._counts[key]

        # Check if threshold reached
        if count >= self._threshold:
            if self._suggestions_file:
                self._suggestions_file.add_or_update(erased_lower, replacement_lower, count)
                if count == self._threshold:
                    logger.info(f"New suggestion: '{erased_lower}' → '{replacement_lower}' (corrected {count} times)")

        return count

    def ignore_pattern(self, typo: str, correction: str) -> bool:
        """Add pattern to ignore list and remove from suggestions."""
        success = True

        if self._ignore_list:
            success = self._ignore_list.add(typo, correction) and success

        if self._suggestions_file:
            success = self._suggestions_file.remove(typo, correction) and success

        return success

    def get_suggestions(self) -> list[tuple[str, str, int]]:
        """Get current suggestions as (typo, correction, count) tuples."""
        if self._suggestions_file:
            return self._suggestions_file.get_all()
        return []

    @property
    def suggestion_count(self) -> int:
        """Number of current suggestions."""
        if self._suggestions_file:
            return len(self._suggestions_file)
        return 0
```

**Acceptance criteria**:
- [ ] Tracks pattern frequency in memory
- [ ] Writes to suggestions.txt at threshold
- [ ] Respects ignore.txt
- [ ] Case-insensitive matching

---

### Task 4: Integrate with main.py

**Goal**: Wire up the correction pattern tracking.

**Files to modify**:
- `src/custom_autocorrect/main.py`

**Changes needed**:

```python
from .suggestions import CorrectionPatternTracker

_pattern_tracker: Optional[CorrectionPatternTracker] = None

def on_correction_pattern(erased: str, replacement: str) -> None:
    """Callback when a correction pattern is detected."""
    global _pattern_tracker

    if _pattern_tracker:
        count = _pattern_tracker.record_pattern(erased, replacement)
        if count:
            logging.getLogger(__name__).debug(
                f"Pattern detected: '{erased}' → '{replacement}' (count: {count})"
            )

def main() -> int:
    global _pattern_tracker

    # ... existing setup ...

    # Initialize pattern tracker
    _pattern_tracker = CorrectionPatternTracker.create_default()
    load_stats = _pattern_tracker.load()

    print(f"Suggestions: {load_stats.get('suggestions', 0)} pending")
    print(f"Ignored patterns: {load_stats.get('ignored', 0)}")

    # ... later, when creating KeystrokeEngine ...
    engine = KeystrokeEngine(
        on_word_complete=on_word_detected,
        on_correction_pattern=on_correction_pattern,  # NEW
    )
```

**Acceptance criteria**:
- [ ] Pattern tracker initialized on startup
- [ ] Callback wired to KeystrokeEngine
- [ ] Stats printed on startup

---

### Task 5: Update Version and Exports

**Files to modify**:
- `src/custom_autocorrect/__init__.py`

**Changes**:
```python
__version__ = "0.6.0"  # Phase 7

from .suggestions import (
    CorrectionPatternTracker,
    IgnoreList,
    SuggestionsFile,
    SUGGESTION_THRESHOLD,
)
```

---

### Task 6: Write Unit Tests

**Files to modify**:
- `tests/test_suggestions.py`

**Test cases**:

```python
class TestIgnoreList:
    def test_load_from_file(self): ...
    def test_is_ignored_case_insensitive(self): ...
    def test_add_pattern_persists(self): ...
    def test_handles_missing_file(self): ...

class TestSuggestionsFile:
    def test_load_parses_format(self): ...
    def test_add_or_update_new(self): ...
    def test_add_or_update_existing(self): ...
    def test_remove_pattern(self): ...
    def test_sorted_by_count(self): ...

class TestCorrectionPatternTracker:
    def test_record_pattern_increments_count(self): ...
    def test_same_word_not_tracked(self): ...
    def test_ignored_pattern_not_tracked(self): ...
    def test_writes_at_threshold(self): ...
    def test_ignore_removes_from_suggestions(self): ...
```

Also update `tests/test_keystroke_engine.py`:

```python
class TestCorrectionPatternDetection:
    def test_backspace_erase_then_retype_triggers_callback(self): ...
    def test_partial_backspace_no_callback(self): ...
    def test_same_word_retyped_no_callback(self): ...
    def test_clear_key_resets_tracking(self): ...
```

---

### Task 7: Write Property-Based Tests (CP4)

**Files to modify**:
- `tests/test_properties.py`

**Property tests**:

```python
class TestCorrectionPatternCP4:
    """Property-based tests for CP4: Correction Pattern Threshold.

    For any pattern in suggestions.txt, it must represent a backspace
    correction that occurred at least SUGGESTION_THRESHOLD times.
    """

    @given(word_text, word_text, st.integers(min_value=1, max_value=4))
    def test_pattern_not_suggested_before_threshold(self, w1, w2, count): ...

    @given(word_text, word_text, st.integers(min_value=5, max_value=20))
    def test_pattern_suggested_at_threshold(self, w1, w2, count): ...

    @given(word_text)
    def test_same_word_never_tracked(self, word): ...

    @given(word_text, word_text)
    def test_ignored_patterns_never_suggested(self, w1, w2): ...
```

---

## File Summary

### Files to Modify
| File | Changes |
|------|---------|
| `word_buffer.py` | Add erased word tracking (optional - may keep in engine) |
| `keystroke_engine.py` | Add backspace detection and on_correction_pattern callback |
| `suggestions.py` | Implement IgnoreList, SuggestionsFile, CorrectionPatternTracker |
| `main.py` | Integrate pattern tracking |
| `__init__.py` | Export new classes, bump version to 0.6.0 |
| `tests/test_suggestions.py` | Replace placeholder with real tests |
| `tests/test_keystroke_engine.py` | Add correction pattern detection tests |
| `tests/test_properties.py` | Add CP4 property tests |

### Files NOT Needed (Removed from Original Plan)
| File | Reason |
|------|--------|
| `resources/words.txt` | No dictionary needed |
| Dictionary class | Not using dictionary approach |
| custom-words.txt support | Not needed without dictionary |

---

## Suggested suggestions.txt Format

```
# Suggested Corrections
# Detected from your typing patterns (backspace corrections)
# To enable: copy the line to rules.txt (remove the count part)
# To ignore: add to ignore.txt
#
teh=the (corrected 12 times)
adn=and (corrected 7 times)
hte=the (corrected 5 times)
```

## Suggested ignore.txt Format

```
# Patterns to never suggest
# Format: typo=correction (one per line)
#
# Example: if you often type "hte" then correct to "http" (not "the"),
# you might want to ignore hte=the
```

---

## Task Order

1. **Task 2**: Modify KeystrokeEngine (core detection logic)
2. **Task 1**: Extend WordBuffer if needed (may fold into Task 2)
3. **Task 3**: Implement CorrectionPatternTracker
4. **Task 6**: Write unit tests for all components
5. **Task 7**: Write property-based tests (CP4)
6. **Task 4**: Integrate with main.py
7. **Task 5**: Update version and exports
8. Manual testing

---

## Acceptance Criteria Summary

From REQ-4 (Pattern Suggestion) - Revised:
- [x] System tracks correction patterns from backspace behavior
- [x] System logs pattern to suggestions.txt after 5+ corrections
- [x] System does NOT auto-create rules (user copies to rules.txt)
- [x] System does NOT suggest ignored patterns

From REQ-5 (Ignore List Management):
- [x] Ignored patterns stored in ignore.txt
- [x] System never suggests ignored patterns
- [ ] Tray menu to view/ignore suggestions (Phase 8 - UI)

---

## Implementation Complete

**Date**: 2026-01-31
**Version**: 0.6.0

### Files Modified
- [keystroke_engine.py](src/custom_autocorrect/keystroke_engine.py) - Added `on_correction_pattern` callback and backspace tracking
- [suggestions.py](src/custom_autocorrect/suggestions.py) - Full implementation of IgnoreList, SuggestionsFile, CorrectionPatternTracker
- [main.py](src/custom_autocorrect/main.py) - Integrated pattern tracking with startup/shutdown
- [__init__.py](src/custom_autocorrect/__init__.py) - Version bump to 0.6.0, added exports

### Test Coverage
- 38 new unit tests for suggestions.py
- 13 new unit tests for correction pattern detection in keystroke_engine.py
- 8 new property-based tests for CP4

### Key Implementation Details
1. **Backspace detection**: Tracks when buffer goes empty via backspaces (not partial erasures)
2. **Pattern matching**: Case-insensitive, stores as lowercase keys
3. **Threshold**: Default 5 occurrences before writing to suggestions.txt
4. **File format**: `typo=correction (corrected N times)`

### Tests Passing
All 318 tests pass (2 skipped for Windows-specific functionality)
