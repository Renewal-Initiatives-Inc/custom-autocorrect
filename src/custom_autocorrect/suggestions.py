"""Pattern suggestion system using backspace detection.

Phase 7 Implementation:
- Tracks correction patterns (erased_word -> new_word) from backspace behavior
- Writes patterns to suggestions.txt after threshold reached
- Supports ignore.txt for patterns to skip

The system detects when users erase a word and type a different word.
After SUGGESTION_THRESHOLD occurrences, the pattern is written to
suggestions.txt for user review. Users can then:
- Copy the pattern to rules.txt to enable autocorrection
- Add it to ignore.txt to stop tracking that pattern
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
# Format: typo=correction (corrected N times)
SUGGESTION_LINE_PATTERN = re.compile(r"^(.+?)=(.+?)\s+\(corrected\s+(\d+)\s+times?\)$")


class IgnoreList:
    """Manages patterns to never suggest.

    The ignore list stores patterns in the format "typo=correction" (one per line).
    Patterns in the ignore list are never written to suggestions.txt.
    """

    def __init__(self, ignore_path: Optional[Path] = None):
        """Initialize the ignore list.

        Args:
            ignore_path: Path to ignore.txt file. If None, operates in memory only.
        """
        self._ignored: set[str] = set()  # Store as "typo=correction" keys
        self._path = ignore_path

    def load(self) -> int:
        """Load ignored patterns from file.

        Returns:
            Number of patterns loaded.
        """
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
        """Check if pattern should be ignored.

        Args:
            typo: The typo word.
            correction: The correction word.

        Returns:
            True if this pattern is in the ignore list.
        """
        key = f"{typo.lower()}={correction.lower()}"
        return key in self._ignored

    def add(self, typo: str, correction: str) -> bool:
        """Add pattern to ignore list.

        Args:
            typo: The typo word.
            correction: The correction word.

        Returns:
            True if successfully added/persisted, False on file error.
        """
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
        """Return number of ignored patterns."""
        return len(self._ignored)


class SuggestionsFile:
    """Manages suggestions.txt file operations.

    The suggestions file stores patterns that have reached the threshold,
    formatted as: typo=correction (corrected N times)
    """

    def __init__(self, path: Optional[Path] = None):
        """Initialize the suggestions file manager.

        Args:
            path: Path to suggestions.txt. If None, operates in memory only.
        """
        self._path = path
        self._suggestions: dict[str, tuple[str, int]] = {}  # key -> (correction, count)

    def _make_key(self, typo: str, correction: str) -> str:
        """Create a normalized key for a pattern."""
        return f"{typo.lower()}={correction.lower()}"

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
                        typo = match.group(1).lower()
                        correction = match.group(2).lower()
                        count = int(match.group(3))
                        key = self._make_key(typo, correction)
                        self._suggestions[key] = (correction, count)
        except OSError as e:
            logger.warning(f"Failed to load suggestions: {e}")

        return len(self._suggestions)

    def add_or_update(self, typo: str, correction: str, count: int) -> bool:
        """Add or update a suggestion.

        Args:
            typo: The typo word.
            correction: The correction word.
            count: Current occurrence count.

        Returns:
            True if successfully saved, False on file error.
        """
        key = self._make_key(typo, correction)
        self._suggestions[key] = (correction.lower(), count)
        return self._save()

    def remove(self, typo: str, correction: str) -> bool:
        """Remove a pattern from suggestions.

        Args:
            typo: The typo word.
            correction: The correction word.

        Returns:
            True if successfully saved (or pattern wasn't present).
        """
        key = self._make_key(typo, correction)
        if key in self._suggestions:
            del self._suggestions[key]
            return self._save()
        return True

    def _save(self) -> bool:
        """Save all suggestions to file.

        Returns:
            True if successful, False on error.
        """
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
        """Get all suggestions as (typo, correction, count) tuples.

        Returns:
            List of tuples sorted by count descending.
        """
        result = []
        for key, (correction, count) in self._suggestions.items():
            typo = key.split("=")[0]
            result.append((typo, correction, count))
        # Sort by count descending
        result.sort(key=lambda x: -x[2])
        return result

    def __len__(self) -> int:
        """Return number of suggestions."""
        return len(self._suggestions)


class CorrectionPatternTracker:
    """Tracks correction patterns and manages suggestions.

    This is the primary interface used by main.py to track patterns
    detected from backspace corrections.

    Usage:
        tracker = CorrectionPatternTracker.create_default()
        tracker.load()

        # Called by KeystrokeEngine when pattern detected
        tracker.record_pattern("teh", "the")

        # After 5 occurrences, pattern is written to suggestions.txt
    """

    def __init__(
        self,
        ignore_list: Optional[IgnoreList] = None,
        suggestions_file: Optional[SuggestionsFile] = None,
        threshold: int = SUGGESTION_THRESHOLD,
    ):
        """Initialize the pattern tracker.

        Args:
            ignore_list: IgnoreList instance for filtering patterns.
            suggestions_file: SuggestionsFile instance for persistence.
            threshold: Number of occurrences before writing to suggestions.
        """
        self._ignore_list = ignore_list
        self._suggestions_file = suggestions_file
        self._threshold = threshold
        self._counts: Counter = Counter()  # "typo=correction" -> count

    @classmethod
    def create_default(cls) -> "CorrectionPatternTracker":
        """Create tracker with default paths from paths module.

        Returns:
            Configured CorrectionPatternTracker instance.
        """
        from .paths import get_suggestions_path, get_ignore_path

        ignore_list = IgnoreList(ignore_path=get_ignore_path())
        suggestions_file = SuggestionsFile(path=get_suggestions_path())

        return cls(
            ignore_list=ignore_list,
            suggestions_file=suggestions_file,
        )

    def load(self) -> dict[str, int]:
        """Load all data files.

        Returns:
            Dictionary with counts: {"ignored": N, "suggestions": M}
        """
        counts = {}

        if self._ignore_list is not None:
            counts["ignored"] = self._ignore_list.load()

        if self._suggestions_file is not None:
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
        if self._ignore_list is not None and self._ignore_list.is_ignored(erased_lower, replacement_lower):
            logger.debug(f"Pattern ignored: '{erased}' -> '{replacement}'")
            return None

        # Track frequency
        key = f"{erased_lower}={replacement_lower}"
        self._counts[key] += 1
        count = self._counts[key]

        # Check if threshold reached
        if count >= self._threshold:
            if self._suggestions_file is not None:
                self._suggestions_file.add_or_update(erased_lower, replacement_lower, count)
                if count == self._threshold:
                    logger.info(
                        f"New suggestion: '{erased_lower}' -> '{replacement_lower}' "
                        f"(corrected {count} times)"
                    )

        return count

    def ignore_pattern(self, typo: str, correction: str) -> bool:
        """Add pattern to ignore list and remove from suggestions.

        Args:
            typo: The typo word.
            correction: The correction word.

        Returns:
            True if successful.
        """
        success = True

        if self._ignore_list is not None:
            success = self._ignore_list.add(typo, correction) and success

        if self._suggestions_file is not None:
            success = self._suggestions_file.remove(typo, correction) and success

        # Also remove from in-memory counts
        key = f"{typo.lower()}={correction.lower()}"
        if key in self._counts:
            del self._counts[key]

        return success

    def get_suggestions(self) -> list[tuple[str, str, int]]:
        """Get current suggestions as (typo, correction, count) tuples.

        Returns:
            List of suggestions sorted by count descending.
        """
        if self._suggestions_file is not None:
            return self._suggestions_file.get_all()
        return []

    @property
    def suggestion_count(self) -> int:
        """Number of current suggestions."""
        if self._suggestions_file is not None:
            return len(self._suggestions_file)
        return 0

    @property
    def threshold(self) -> int:
        """Get the suggestion threshold."""
        return self._threshold
