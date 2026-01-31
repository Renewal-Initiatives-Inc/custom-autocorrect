# Phase 7: Pattern Suggestion System - Execution Plan

## Overview

**Goal**: Track potential typos (non-dictionary words typed 5+ times) and log suggestions.

**Key Principle**: Never auto-create rules. The system suggests patterns; users confirm everything.

**Requirements Addressed**:
- REQ-4: Pattern Suggestion
- REQ-5: Ignore List Management (partial - file support only; UI in Phase 8)

**Correctness Property**:
- CP4: For any word appearing in suggestions.txt, that word must have been typed at least 5 times AND not be in the dictionary, custom-words.txt, or ignore.txt.

---

## Dependencies Check

Before starting Phase 7, verify these Phase 1-5 deliverables are working:

- [ ] `paths.py` provides `get_suggestions_path()`, `get_ignore_path()`, `get_custom_words_path()`
- [ ] `main.py` has `on_word_detected()` callback where we can integrate suggestion tracking
- [ ] Test infrastructure (pytest, hypothesis) is working
- [ ] App folder creation (`ensure_app_folder()`) works

---

## Task Breakdown

### Task 1: Bundle English Word List (Dictionary)

**Goal**: Include a word list file that can be bundled with the executable.

**Files to create**:
- `resources/words.txt` - English word list (~10,000-50,000 common words)

**Source options** (in order of preference):
1. Download from https://github.com/dwyl/english-words (public domain)
2. Use system words file (`/usr/share/dict/words` equivalent)
3. Create minimal list from common word frequency lists

**Acceptance criteria**:
- [ ] File contains one word per line, lowercase
- [ ] At least 10,000 common English words included
- [ ] No duplicate entries
- [ ] UTF-8 encoded

**Notes**:
- Keep file size reasonable (<500KB) for bundling
- Can be expanded later; start with common words

---

### Task 2: Implement Dictionary Loader

**Goal**: Load the bundled dictionary and custom-words.txt for lookups.

**Files to modify**:
- `src/custom_autocorrect/suggestions.py` - Add dictionary loading

**Implementation**:

```python
# suggestions.py additions

from pathlib import Path
from typing import Optional, Set
import logging

logger = logging.getLogger(__name__)

# Constants
SUGGESTION_THRESHOLD = 5

def get_bundled_dictionary_path() -> Path:
    """Get path to bundled dictionary file."""
    # In bundled exe, use pkg_resources or __file__
    # In dev, use relative path from package
    return Path(__file__).parent.parent.parent / "resources" / "words.txt"

class Dictionary:
    """Manages word lookup across bundled dictionary and custom words."""

    def __init__(
        self,
        dictionary_path: Optional[Path] = None,
        custom_words_path: Optional[Path] = None,
    ):
        self._words: Set[str] = set()
        self._dictionary_path = dictionary_path or get_bundled_dictionary_path()
        self._custom_words_path = custom_words_path

    def load(self) -> int:
        """Load words from dictionary and custom-words.txt.

        Returns:
            Number of words loaded.
        """
        self._words.clear()

        # Load bundled dictionary
        if self._dictionary_path.exists():
            self._load_word_file(self._dictionary_path)

        # Load custom words (if path provided and exists)
        if self._custom_words_path and self._custom_words_path.exists():
            self._load_word_file(self._custom_words_path)

        return len(self._words)

    def _load_word_file(self, path: Path) -> None:
        """Load words from a file (one word per line)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        self._words.add(word)
        except OSError as e:
            logger.warning(f"Failed to load word file {path}: {e}")

    def contains(self, word: str) -> bool:
        """Check if word is in dictionary (case-insensitive)."""
        return word.lower() in self._words

    def __len__(self) -> int:
        return len(self._words)
```

**Acceptance criteria**:
- [ ] Loads bundled dictionary on startup
- [ ] Loads custom-words.txt if present
- [ ] Case-insensitive lookup
- [ ] Handles missing files gracefully
- [ ] Handles malformed files (logs warning, continues)

---

### Task 3: Implement Ignore List Support

**Goal**: Load ignore.txt and check words against it.

**Files to modify**:
- `src/custom_autocorrect/suggestions.py` - Add ignore list support

**Implementation**:

```python
class IgnoreList:
    """Manages the list of words to never suggest."""

    def __init__(self, ignore_path: Optional[Path] = None):
        self._ignored: Set[str] = set()
        self._path = ignore_path

    def load(self) -> int:
        """Load ignored words from file.

        Returns:
            Number of words loaded.
        """
        self._ignored.clear()

        if not self._path or not self._path.exists():
            return 0

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        self._ignored.add(word)
        except OSError as e:
            logger.warning(f"Failed to load ignore list {self._path}: {e}")

        return len(self._ignored)

    def is_ignored(self, word: str) -> bool:
        """Check if word should be ignored (case-insensitive)."""
        return word.lower() in self._ignored

    def add(self, word: str) -> bool:
        """Add word to ignore list and save to file.

        Returns:
            True if added successfully, False otherwise.
        """
        word_lower = word.lower()
        if word_lower in self._ignored:
            return True  # Already ignored

        self._ignored.add(word_lower)

        if self._path:
            try:
                with open(self._path, "a", encoding="utf-8") as f:
                    f.write(f"{word_lower}\n")
                return True
            except OSError as e:
                logger.warning(f"Failed to save ignore word: {e}")
                return False
        return True

    def __len__(self) -> int:
        return len(self._ignored)
```

**Acceptance criteria**:
- [ ] Loads ignore.txt on startup
- [ ] Case-insensitive matching
- [ ] Can add new words (appends to file)
- [ ] Handles missing file gracefully

---

### Task 4: Implement Word Frequency Counter

**Goal**: Track how many times each non-dictionary word is typed.

**Files to modify**:
- `src/custom_autocorrect/suggestions.py` - Add frequency tracking

**Implementation**:

```python
from collections import Counter

class WordFrequencyTracker:
    """Tracks frequency of non-dictionary words typed."""

    def __init__(self):
        self._counts: Counter = Counter()

    def record(self, word: str) -> int:
        """Record a word occurrence.

        Args:
            word: The word that was typed.

        Returns:
            New count for this word.
        """
        word_lower = word.lower()
        self._counts[word_lower] += 1
        return self._counts[word_lower]

    def get_count(self, word: str) -> int:
        """Get current count for a word."""
        return self._counts[word.lower()]

    def get_frequent_words(self, threshold: int = SUGGESTION_THRESHOLD) -> list[tuple[str, int]]:
        """Get words typed at least `threshold` times.

        Returns:
            List of (word, count) tuples, sorted by count descending.
        """
        return [
            (word, count)
            for word, count in self._counts.most_common()
            if count >= threshold
        ]

    def clear(self) -> None:
        """Clear all counts."""
        self._counts.clear()

    def __len__(self) -> int:
        """Number of unique words tracked."""
        return len(self._counts)
```

**Acceptance criteria**:
- [ ] Counts words case-insensitively
- [ ] Returns updated count after recording
- [ ] Can retrieve words above threshold
- [ ] Memory-efficient for typical usage

---

### Task 5: Implement Suggestions Writer

**Goal**: Write words that hit the threshold to suggestions.txt.

**Files to modify**:
- `src/custom_autocorrect/suggestions.py` - Add suggestion file writer

**Implementation**:

```python
import re
from datetime import datetime

# File format patterns
SUGGESTION_LINE_PATTERN = re.compile(r"^(.+?)\s+\(typed\s+(\d+)\s+times?\)$")

class SuggestionsFile:
    """Manages suggestions.txt file operations."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path
        self._suggestions: dict[str, int] = {}  # word -> count

    def load(self) -> int:
        """Load existing suggestions from file.

        Returns:
            Number of suggestions loaded.
        """
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
                        word = match.group(1).lower()
                        count = int(match.group(2))
                        self._suggestions[word] = count
        except OSError as e:
            logger.warning(f"Failed to load suggestions: {e}")

        return len(self._suggestions)

    def contains(self, word: str) -> bool:
        """Check if word is already suggested."""
        return word.lower() in self._suggestions

    def add_or_update(self, word: str, count: int) -> bool:
        """Add or update a suggestion.

        Args:
            word: The word to suggest.
            count: Current frequency count.

        Returns:
            True if saved successfully.
        """
        word_lower = word.lower()
        self._suggestions[word_lower] = count
        return self._save()

    def remove(self, word: str) -> bool:
        """Remove a word from suggestions.

        Returns:
            True if removed and saved successfully.
        """
        word_lower = word.lower()
        if word_lower in self._suggestions:
            del self._suggestions[word_lower]
            return self._save()
        return True

    def _save(self) -> bool:
        """Save all suggestions to file."""
        if not self._path:
            return False

        try:
            with open(self._path, "w", encoding="utf-8") as f:
                f.write("# Pattern Suggestions\n")
                f.write("# Words typed 5+ times that aren't in dictionary\n")
                f.write("# Add to rules.txt to create a correction, or ignore via tray menu\n")
                f.write("#\n")

                # Sort by count descending, then alphabetically
                sorted_suggestions = sorted(
                    self._suggestions.items(),
                    key=lambda x: (-x[1], x[0])
                )

                for word, count in sorted_suggestions:
                    f.write(f"{word} (typed {count} times)\n")

            return True
        except OSError as e:
            logger.warning(f"Failed to save suggestions: {e}")
            return False

    def get_all(self) -> list[tuple[str, int]]:
        """Get all suggestions as (word, count) pairs."""
        return list(self._suggestions.items())

    def __len__(self) -> int:
        return len(self._suggestions)
```

**Acceptance criteria**:
- [ ] Parses existing suggestions.txt format
- [ ] Writes in format: `word (typed N times)`
- [ ] Updates count if word already suggested
- [ ] Sorts by count (descending)
- [ ] Handles file errors gracefully

---

### Task 6: Implement SuggestionTracker (Main Integration Class)

**Goal**: Orchestrate all suggestion components; provide single interface for main.py.

**Files to modify**:
- `src/custom_autocorrect/suggestions.py` - Add main tracker class

**Implementation**:

```python
class SuggestionTracker:
    """Main class for tracking potential typos and managing suggestions.

    This is the primary interface used by main.py to track words
    that might be typos worth suggesting to the user.
    """

    def __init__(
        self,
        dictionary: Optional[Dictionary] = None,
        ignore_list: Optional[IgnoreList] = None,
        suggestions_file: Optional[SuggestionsFile] = None,
        threshold: int = SUGGESTION_THRESHOLD,
    ):
        self._dictionary = dictionary
        self._ignore_list = ignore_list
        self._suggestions_file = suggestions_file
        self._frequency = WordFrequencyTracker()
        self._threshold = threshold

    @classmethod
    def create_default(cls) -> "SuggestionTracker":
        """Create tracker with default paths from paths module."""
        from .paths import (
            get_suggestions_path,
            get_ignore_path,
            get_custom_words_path,
        )

        dictionary = Dictionary(
            custom_words_path=get_custom_words_path(),
        )
        ignore_list = IgnoreList(ignore_path=get_ignore_path())
        suggestions_file = SuggestionsFile(path=get_suggestions_path())

        return cls(
            dictionary=dictionary,
            ignore_list=ignore_list,
            suggestions_file=suggestions_file,
        )

    def load(self) -> dict[str, int]:
        """Load all data files.

        Returns:
            Dict with counts: {"dictionary": N, "ignored": N, "suggestions": N}
        """
        counts = {}

        if self._dictionary:
            counts["dictionary"] = self._dictionary.load()

        if self._ignore_list:
            counts["ignored"] = self._ignore_list.load()

        if self._suggestions_file:
            counts["suggestions"] = self._suggestions_file.load()

        return counts

    def track_word(self, word: str) -> Optional[int]:
        """Track a typed word and potentially add to suggestions.

        This is called for every word typed that doesn't match a correction rule.

        Args:
            word: The typed word.

        Returns:
            Current count if word is being tracked, None if word is valid/ignored.
        """
        word_lower = word.lower()

        # Skip if in dictionary
        if self._dictionary and self._dictionary.contains(word_lower):
            return None

        # Skip if ignored
        if self._ignore_list and self._ignore_list.is_ignored(word_lower):
            return None

        # Track frequency
        count = self._frequency.record(word_lower)

        # Check if threshold reached
        if count >= self._threshold:
            if self._suggestions_file:
                # Add or update in suggestions file
                already_suggested = self._suggestions_file.contains(word_lower)
                self._suggestions_file.add_or_update(word_lower, count)

                if not already_suggested:
                    logger.info(f"New suggestion: '{word_lower}' (typed {count} times)")

        return count

    def is_valid_word(self, word: str) -> bool:
        """Check if word is in dictionary or custom words."""
        if self._dictionary:
            return self._dictionary.contains(word)
        return False

    def is_ignored(self, word: str) -> bool:
        """Check if word is in ignore list."""
        if self._ignore_list:
            return self._ignore_list.is_ignored(word)
        return False

    def ignore_word(self, word: str) -> bool:
        """Add word to ignore list and remove from suggestions.

        Returns:
            True if successful.
        """
        success = True

        if self._ignore_list:
            success = self._ignore_list.add(word) and success

        if self._suggestions_file:
            success = self._suggestions_file.remove(word) and success

        return success

    def get_suggestions(self) -> list[tuple[str, int]]:
        """Get current suggestions as (word, count) pairs."""
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
- [ ] Single point of integration for main.py
- [ ] Loads all files on startup
- [ ] Tracks words correctly (dictionary check → ignore check → count)
- [ ] Writes to suggestions.txt when threshold reached
- [ ] Can ignore words (removes from suggestions, adds to ignore)

---

### Task 7: Integrate with main.py

**Goal**: Call SuggestionTracker from the `on_word_detected()` callback.

**Files to modify**:
- `src/custom_autocorrect/main.py` - Add suggestion tracking

**Changes needed**:

1. Import SuggestionTracker
2. Add global `_suggestion_tracker` instance
3. Initialize in `main()` after rule loading
4. Call `track_word()` in `on_word_detected()` when no rule matches

```python
# In main.py - changes needed

from .suggestions import SuggestionTracker

_suggestion_tracker: Optional[SuggestionTracker] = None

def on_word_detected(word: str) -> None:
    global _matcher, _correction_engine, _suggestion_tracker

    # ... existing correction logic ...

    if rule:
        # Perform correction (existing code)
        ...
    else:
        # No rule match - track for suggestions (NEW)
        if _suggestion_tracker:
            _suggestion_tracker.track_word(word)

        logging.getLogger(__name__).debug(f"No rule match for: '{word}'")

def main() -> int:
    global _suggestion_tracker

    # ... existing setup ...

    # Initialize suggestion tracker (NEW)
    _suggestion_tracker = SuggestionTracker.create_default()
    load_stats = _suggestion_tracker.load()

    print(f"Dictionary: {load_stats.get('dictionary', 0)} words")
    print(f"Suggestions: {load_stats.get('suggestions', 0)} pending")

    # ... rest of main ...
```

**Acceptance criteria**:
- [ ] SuggestionTracker initialized on startup
- [ ] Stats printed showing dictionary size and pending suggestions
- [ ] `track_word()` called for every non-matching word
- [ ] No performance impact on correction flow

---

### Task 8: Update Version and __init__.py

**Files to modify**:
- `src/custom_autocorrect/__init__.py` - Update version, export new classes

**Changes**:
```python
__version__ = "0.5.0"

from .suggestions import (
    Dictionary,
    IgnoreList,
    SuggestionTracker,
    SuggestionsFile,
    WordFrequencyTracker,
    SUGGESTION_THRESHOLD,
)
```

---

### Task 9: Write Unit Tests

**Files to create/modify**:
- `tests/test_suggestions.py` - Replace placeholder with real tests

**Test cases needed**:

```python
# Dictionary tests
class TestDictionary:
    def test_load_bundled_dictionary(self): ...
    def test_load_custom_words(self): ...
    def test_contains_case_insensitive(self): ...
    def test_handles_missing_file(self): ...
    def test_ignores_comments(self): ...
    def test_ignores_blank_lines(self): ...

# IgnoreList tests
class TestIgnoreList:
    def test_load_from_file(self): ...
    def test_is_ignored_case_insensitive(self): ...
    def test_add_word_persists(self): ...
    def test_handles_missing_file(self): ...

# WordFrequencyTracker tests
class TestWordFrequencyTracker:
    def test_record_increments_count(self): ...
    def test_record_case_insensitive(self): ...
    def test_get_frequent_words_threshold(self): ...
    def test_get_frequent_words_sorted(self): ...
    def test_clear_resets_counts(self): ...

# SuggestionsFile tests
class TestSuggestionsFile:
    def test_load_parses_format(self): ...
    def test_add_or_update_new(self): ...
    def test_add_or_update_existing(self): ...
    def test_remove_word(self): ...
    def test_save_format(self): ...
    def test_sorted_by_count(self): ...

# SuggestionTracker tests
class TestSuggestionTracker:
    def test_track_word_in_dictionary_returns_none(self): ...
    def test_track_word_ignored_returns_none(self): ...
    def test_track_word_increments_count(self): ...
    def test_track_word_adds_to_suggestions_at_threshold(self): ...
    def test_ignore_word_removes_from_suggestions(self): ...
    def test_create_default_uses_paths(self): ...
```

**Acceptance criteria**:
- [ ] All unit tests pass
- [ ] Tests use temporary files (not real Documents folder)
- [ ] Edge cases covered (empty files, missing files, malformed input)

---

### Task 10: Write Property-Based Tests (CP4)

**Files to modify**:
- `tests/test_properties.py` - Add CP4 tests

**Property tests for CP4 (Suggestion Threshold)**:

```python
class TestSuggestionThresholdCP4:
    """Property-based tests for CP4: Suggestion Threshold.

    For any word appearing in suggestions.txt, that word must have been
    typed at least 5 times AND not be in dictionary, custom-words, or ignore.
    """

    @given(st.lists(word_text, min_size=1, max_size=20))
    def test_word_not_suggested_before_threshold(self, words: list):
        """Words typed fewer than threshold times are never suggested."""
        ...

    @given(word_text, st.integers(min_value=5, max_value=100))
    def test_word_suggested_at_threshold(self, word: str, count: int):
        """Words typed threshold+ times appear in suggestions."""
        ...

    @given(word_text)
    def test_dictionary_words_never_suggested(self, word: str):
        """Words in dictionary are never tracked."""
        ...

    @given(word_text)
    def test_ignored_words_never_suggested(self, word: str):
        """Ignored words are never tracked."""
        ...

    @given(st.lists(word_text, min_size=5, max_size=50))
    def test_suggestion_count_accurate(self, words: list):
        """Suggestion count matches words at or above threshold."""
        ...
```

**Acceptance criteria**:
- [ ] All property tests pass
- [ ] Tests verify CP4 correctness property holds

---

### Task 11: Create Sample Dictionary File

**Files to create**:
- `resources/words.txt` - Download or create word list

**Steps**:
1. Download common English words list (e.g., from dwyl/english-words)
2. Filter to ~10,000-50,000 most common words
3. Clean: lowercase, remove duplicates, one word per line
4. Save as UTF-8 text file

**Alternative**: Start with a minimal list (~5,000 words) and expand later.

---

### Task 12: Manual Testing

**Test scenarios**:

1. **Basic suggestion flow**:
   - Type a non-dictionary word 5 times (e.g., "xyzabc")
   - Verify it appears in `Documents/CustomAutocorrect/suggestions.txt`

2. **Dictionary bypass**:
   - Type "hello" 10 times
   - Verify it does NOT appear in suggestions (it's in dictionary)

3. **Custom words**:
   - Add "mycompany" to `custom-words.txt`
   - Type "mycompany" 10 times
   - Verify it does NOT appear in suggestions

4. **Ignore list**:
   - Type "testword" 5 times (appears in suggestions)
   - Add "testword" to `ignore.txt`
   - Restart app
   - Type "testword" 10 more times
   - Verify it's not in suggestions

5. **Correction still works**:
   - Add rule `teh=the` to rules.txt
   - Type "teh " and verify correction
   - Verify "teh" is NOT tracked for suggestions (corrections don't go to suggestions)

---

## File Summary

### Files to Create
| File | Purpose |
|------|---------|
| `resources/words.txt` | Bundled English dictionary (~10K-50K words) |

### Files to Modify
| File | Changes |
|------|---------|
| `src/custom_autocorrect/suggestions.py` | Implement all suggestion classes |
| `src/custom_autocorrect/main.py` | Integrate SuggestionTracker |
| `src/custom_autocorrect/__init__.py` | Export new classes, bump version |
| `tests/test_suggestions.py` | Replace placeholder with real tests |
| `tests/test_properties.py` | Add CP4 property tests |

### Files Unchanged
| File | Reason |
|------|--------|
| `paths.py` | Already has all needed path functions |
| `keystroke_engine.py` | No changes needed |
| `rules.py` | No changes needed |
| `correction.py` | No changes needed |
| `correction_log.py` | No changes needed |

---

## Estimated Task Order

1. **Task 11**: Create dictionary file first (needed for testing)
2. **Task 2**: Dictionary class (can test immediately)
3. **Task 3**: IgnoreList class
4. **Task 4**: WordFrequencyTracker
5. **Task 5**: SuggestionsFile
6. **Task 6**: SuggestionTracker (orchestration)
7. **Task 9**: Unit tests for all classes
8. **Task 10**: Property-based tests (CP4)
9. **Task 7**: Integrate with main.py
10. **Task 8**: Update version
11. **Task 12**: Manual testing
12. **Task 1**: Verify dictionary bundling works (may need PyInstaller adjustments later)

---

## Acceptance Criteria Summary

From REQ-4 (Pattern Suggestion):
- [x] System maintains built-in English word list (Task 1, 2)
- [x] System tracks words typed not in dictionary or custom words (Task 4, 6)
- [x] System logs word to suggestions.txt after typed 5+ times (Task 5, 6)
- [x] System does NOT auto-create rules (verified by design)
- [x] System does NOT suggest ignored words (Task 3, 6)
- [x] System allows custom-words.txt additions (Task 2)

From REQ-5 (Ignore List Management):
- [x] Ignored words stored in ignore.txt (Task 3)
- [x] System never suggests words in ignore.txt (Task 6)
- [ ] Tray menu to view/ignore suggestions (Phase 8 - UI)

---

## Notes for Implementation

1. **Performance**: Word tracking happens on every typed word. Keep operations O(1) using sets/dicts.

2. **Memory**: WordFrequencyTracker keeps all non-dictionary words in memory. For typical usage (~1000 unique non-dictionary words per session), this is fine.

3. **Thread Safety**: Current design is single-threaded (keyboard callback). If issues arise, consider locks around file operations.

4. **File Format**: Match the format specified in requirements.md for suggestions.txt:
   ```
   # Words typed 5+ times that aren't in dictionary
   xyzword (typed 7 times)
   anothertypo (typed 5 times)
   ```

5. **Case Sensitivity**: All lookups are case-insensitive. Store everything lowercase internally.

6. **Bundling Dictionary**: For PyInstaller, may need to adjust how `get_bundled_dictionary_path()` finds the file. This is Phase 10 concern but design for it now.
