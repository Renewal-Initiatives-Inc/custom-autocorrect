"""Rule loading, parsing, and matching.

This module provides:
- RuleParser: Parse rules.txt format (typo=correction)
- RuleMatcher: Match typed words against loaded rules
- RuleFileWatcher: Watch for file changes and reload

Correctness Properties:
- CP1: Rule Integrity - corrections only for exact rule matches
- CP2: Whole-Word Guarantee - substring matches do NOT trigger corrections
  (already satisfied by KeystrokeEngine's word extraction)
"""

import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .paths import get_rules_path, get_app_folder

logger = logging.getLogger(__name__)

# Backup file name
RULES_BACKUP_NAME = "rules.txt.bak"


@dataclass(frozen=True)
class Rule:
    """A single correction rule.

    Attributes:
        typo: The misspelled word (stored lowercase for lookup).
        correction: The correct replacement.
        original_typo: The typo as it appeared in the file (preserves case for logging).
    """

    typo: str
    correction: str
    original_typo: str


@dataclass
class RuleParseError:
    """Information about a parsing error.

    Not an exception - we continue parsing and collect errors.
    Following Design Principle P4 (Fail Safe): skip invalid lines.
    """

    line_number: int
    line: str
    reason: str


class RuleParser:
    """Parses rules.txt format.

    Format:
        - typo=correction (one per line)
        - Lines starting with # are comments
        - Blank lines are ignored
        - Invalid lines are skipped with a warning
    """

    @staticmethod
    def parse_line(line: str) -> Optional[Rule]:
        """Parse a single line into a Rule.

        Args:
            line: A line from rules.txt.

        Returns:
            Rule if valid, None if comment/blank/invalid.
        """
        # Strip whitespace
        line = line.strip()

        # Skip empty lines
        if not line:
            return None

        # Skip comments
        if line.startswith("#"):
            return None

        # Must contain =
        if "=" not in line:
            return None

        # Split on first = only (allow = in correction)
        parts = line.split("=", 1)
        if len(parts) != 2:
            return None

        typo = parts[0].strip()
        correction = parts[1].strip()

        # Both must be non-empty
        if not typo or not correction:
            return None

        # Typo must not equal correction (case-insensitive check)
        if typo.lower() == correction.lower():
            return None

        return Rule(
            typo=typo.lower(),  # Lowercase for lookup
            correction=correction,
            original_typo=typo,  # Preserve original for logging
        )

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
        rules: Dict[str, Rule] = {}
        errors: List[RuleParseError] = []

        if not path.exists():
            logger.warning(f"Rules file not found: {path}")
            return rules, errors

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            logger.error(f"Failed to read rules file {path}: {e}")
            return rules, errors
        except UnicodeDecodeError as e:
            logger.error(f"Rules file encoding error {path}: {e}")
            return rules, errors

        for line_num, line in enumerate(lines, start=1):
            # Skip empty and comment lines silently
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            rule = RuleParser.parse_line(line)

            if rule is None:
                # Invalid format - record error
                errors.append(
                    RuleParseError(
                        line_number=line_num,
                        line=line,
                        reason="Invalid rule format (expected: typo=correction)",
                    )
                )
            else:
                # Check for duplicate typos
                if rule.typo in rules:
                    logger.debug(
                        f"Duplicate rule for '{rule.typo}' at line {line_num}, "
                        f"using latest definition"
                    )
                rules[rule.typo] = rule

        return rules, errors


class RuleMatcher:
    """Matches typed words against correction rules.

    Implements:
    - CP1: Rule Integrity (exact match only)
    - CP2: Whole-Word Guarantee (already satisfied by KeystrokeEngine)

    Thread Safety: Not thread-safe. Reload should only happen from main thread
    or be synchronized externally.
    """

    def __init__(self, rules_path: Optional[Path] = None):
        """Initialize with optional path to rules file.

        Args:
            rules_path: Path to rules.txt. If None, uses default location.
        """
        self._rules: Dict[str, Rule] = {}
        self._rules_path = rules_path or get_rules_path()
        self._parse_errors: List[RuleParseError] = []
        self._last_modified: float = 0.0

    @property
    def rules_path(self) -> Path:
        """Get the path to the rules file."""
        return self._rules_path

    def load(self) -> int:
        """Load rules from the rules file.

        Returns:
            Number of rules loaded.
        """
        self._rules, self._parse_errors = RuleParser.parse_file(self._rules_path)

        # Update last modified time
        try:
            self._last_modified = self._rules_path.stat().st_mtime
        except OSError:
            self._last_modified = 0.0

        if self._parse_errors:
            logger.warning(
                f"Found {len(self._parse_errors)} parse errors in rules file"
            )

        logger.info(f"Loaded {len(self._rules)} rules from {self._rules_path}")
        return len(self._rules)

    def reload_if_changed(self) -> bool:
        """Reload rules if the file has been modified.

        Returns:
            True if rules were reloaded, False otherwise.
        """
        try:
            current_mtime = self._rules_path.stat().st_mtime
        except OSError:
            # File might be temporarily unavailable
            return False

        if current_mtime > self._last_modified:
            logger.info("Rules file changed, reloading...")
            self.load()
            return True

        return False

    def match(self, word: str) -> Optional[Rule]:
        """Check if a word matches a correction rule.

        Case-insensitive matching: "TEH" matches rule for "teh".

        Args:
            word: The word to check (from KeystrokeEngine).

        Returns:
            The matching Rule if found, None otherwise.
        """
        return self._rules.get(word.lower())

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

    def get_all_rules(self) -> List[Rule]:
        """Get all loaded rules."""
        return list(self._rules.values())


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
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running

    def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            logger.warning("RuleFileWatcher already running")
            return

        self._running = True
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._watch_loop,
            name="RuleFileWatcher",
            daemon=True,  # Don't prevent program exit
        )
        self._thread.start()
        logger.info(
            f"Started file watcher (poll interval: {self._poll_interval}s)"
        )

    def stop(self) -> None:
        """Stop watching."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        if self._thread:
            # Give the thread a moment to exit cleanly
            self._thread.join(timeout=self._poll_interval + 0.5)
            self._thread = None

        logger.info("Stopped file watcher")

    def _watch_loop(self) -> None:
        """Background thread that polls for file changes."""
        while self._running:
            try:
                # Check if file changed
                if self._matcher.reload_if_changed():
                    # Backup before reload (only if we have valid rules)
                    if self._matcher.rule_count > 0:
                        create_backup()
                    logger.info(
                        f"Rules reloaded: {self._matcher.rule_count} rules active"
                    )
            except Exception as e:
                logger.error(f"Error checking for rule file changes: {e}")

            # Wait for poll interval or stop signal
            if self._stop_event.wait(timeout=self._poll_interval):
                break  # Stop signal received


# =============================================================================
# Backup and Restore Functions
# =============================================================================

def get_backup_path() -> Path:
    """Get the path to the rules backup file.

    Returns:
        Path to rules.txt.bak in the app folder.
    """
    return get_app_folder() / RULES_BACKUP_NAME


def backup_exists() -> bool:
    """Check if a rules backup file exists.

    Returns:
        True if backup exists, False otherwise.
    """
    return get_backup_path().exists()


def create_backup() -> bool:
    """Create a backup of the current rules file.

    Only creates backup if rules file exists and has valid rules.

    Returns:
        True if backup created, False otherwise.
    """
    rules_path = get_rules_path()
    backup_path = get_backup_path()

    if not rules_path.exists():
        logger.debug("No rules file to backup")
        return False

    # Verify the rules file has valid content
    rules, errors = RuleParser.parse_file(rules_path)
    if not rules:
        logger.debug("Rules file is empty or invalid, skipping backup")
        return False

    try:
        import shutil
        shutil.copy2(rules_path, backup_path)
        logger.info(f"Created rules backup: {backup_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create rules backup: {e}")
        return False


def restore_from_backup() -> bool:
    """Restore rules from backup file.

    Returns:
        True if restore successful, False otherwise.
    """
    rules_path = get_rules_path()
    backup_path = get_backup_path()

    if not backup_path.exists():
        logger.error("No backup file to restore from")
        return False

    try:
        import shutil
        shutil.copy2(backup_path, rules_path)
        logger.info(f"Restored rules from backup: {backup_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to restore rules from backup: {e}")
        return False


def get_backup_info() -> Optional[Dict]:
    """Get information about the backup file.

    Returns:
        Dictionary with backup info, or None if no backup.
    """
    backup_path = get_backup_path()

    if not backup_path.exists():
        return None

    try:
        stat = backup_path.stat()
        rules, _ = RuleParser.parse_file(backup_path)

        from datetime import datetime
        mtime = datetime.fromtimestamp(stat.st_mtime)

        return {
            "path": backup_path,
            "modified": mtime,
            "rule_count": len(rules),
            "size_bytes": stat.st_size,
        }
    except Exception as e:
        logger.error(f"Error getting backup info: {e}")
        return None
