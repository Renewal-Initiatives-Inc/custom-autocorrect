"""Main entry point for Custom Autocorrect.

Phase 9: Captures keystrokes, matches words against rules, performs corrections,
logs corrections to a rolling log file, skips password fields, tracks
correction patterns from backspace behavior, provides system tray integration,
and supports adding rules via Win+Shift+A hotkey.

Features:
- Real-time keystroke monitoring and autocorrection
- Password field detection to avoid corrections in sensitive contexts
- Hot reload of rules.txt without restart
- Pattern detection for learning new corrections
- System tray icon with menu for quick access
- Win+Shift+A hotkey for adding new rules
"""

import logging
import sys
import threading
from typing import Optional

from .correction import CorrectionEngine, apply_casing
from .correction_log import log_correction
from .hotkey import AddRuleHotkey
from .keystroke_engine import KeystrokeEngine
from .password_detect import is_password_field
from .paths import ensure_app_folder, ensure_rules_file, get_rules_path
from .rules import RuleFileWatcher, RuleMatcher, Rule
from .suggestions import CorrectionPatternTracker
from .tray import SystemTray

# Global instances for the word detection callback
_matcher: Optional[RuleMatcher] = None
_correction_engine: Optional[CorrectionEngine] = None
_pattern_tracker: Optional[CorrectionPatternTracker] = None
_tray: Optional[SystemTray] = None
_hotkey: Optional[AddRuleHotkey] = None


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application.

    Args:
        debug: If True, enable debug-level logging.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def on_correction_pattern(erased: str, replacement: str) -> None:
    """Callback when a correction pattern is detected.

    Phase 7: Called when user erases a word via backspace and types
    a different word. Records the pattern for potential suggestion.

    Args:
        erased: The word that was erased.
        replacement: The word typed to replace it.
    """
    global _pattern_tracker

    if _pattern_tracker:
        count = _pattern_tracker.record_pattern(erased, replacement)
        if count:
            logging.getLogger(__name__).debug(
                f"Pattern detected: '{erased}' -> '{replacement}' (count: {count})"
            )


def on_word_detected(word: str) -> None:
    """Callback when a word is completed (space pressed).

    Phase 6: Check for password field, then check against correction rules
    and perform correction if matched.

    Args:
        word: The completed word (without trailing space).
    """
    global _matcher, _correction_engine

    if _matcher is None or _correction_engine is None:
        return

    # CP7: Password Field Safety - skip corrections in password fields
    if is_password_field():
        logging.getLogger(__name__).debug(
            f"Skipped correction in password field: '{word}'"
        )
        return

    rule = _matcher.match(word)

    if rule:
        # Phase 4: Perform the actual correction
        success = _correction_engine.correct(word, rule.correction)

        if success:
            # Phase 5: Log the correction to corrections.log
            # Apply same casing logic used in correction engine
            cased_correction = apply_casing(word, rule.correction)
            log_correction(word, cased_correction)

            logging.getLogger(__name__).info(
                f"Corrected: '{word}' -> '{cased_correction}' "
                f"(count: {_correction_engine.correction_count})"
            )
        else:
            logging.getLogger(__name__).warning(
                f"Failed to correct: '{word}' -> '{rule.correction}'"
            )
    else:
        # Debug logging for non-matches
        logging.getLogger(__name__).debug(f"No rule match for: '{word}'")


def main() -> int:
    """Start the Custom Autocorrect application.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    global _matcher, _correction_engine, _pattern_tracker, _tray, _hotkey

    # Check for debug flag
    debug = "--debug" in sys.argv or "-d" in sys.argv

    setup_logging(debug=debug)
    logger = logging.getLogger(__name__)

    print("Custom Autocorrect v0.9.0 - Phase 9")
    print("=" * 50)
    print()

    # Phase 3: Set up app folder and rules
    try:
        ensure_app_folder()
        ensure_rules_file()
    except OSError as e:
        print(f"Error: Failed to create app folder: {e}")
        return 1

    # Load rules
    _matcher = RuleMatcher()
    rule_count = _matcher.load()

    rules_path = _matcher.rules_path
    print(f"Rules file: {rules_path}")
    print(f"Loaded {rule_count} correction rule(s)")
    print()

    # Report any parse errors
    for error in _matcher.get_parse_errors():
        print(f"  Warning: Line {error.line_number}: {error.reason}")
        print(f"           {error.line}")

    if rule_count == 0:
        print("Tip: Add rules to rules.txt in format: typo=correction")
        print("     Example: teh=the")
    print()

    # Phase 7: Initialize pattern tracker
    _pattern_tracker = CorrectionPatternTracker.create_default()
    pattern_stats = _pattern_tracker.load()
    print(f"Suggestions: {pattern_stats.get('suggestions', 0)} pending")
    print(f"Ignored patterns: {pattern_stats.get('ignored', 0)}")
    print()

    # Phase 4: Initialize correction engine
    _correction_engine = CorrectionEngine(delay_ms=0)

    # Phase 8: Create shutdown event for clean exit
    shutdown_event = threading.Event()

    # Phase 8: Initialize system tray
    try:
        _tray = SystemTray(
            pattern_tracker=_pattern_tracker,
            on_exit=shutdown_event.set,
        )
        _tray.start()
        print("System tray icon active - right-click for options")
    except ImportError as e:
        print(f"Warning: System tray unavailable: {e}")
        _tray = None

    # Phase 9: Initialize add-rule hotkey
    def on_rule_added(typo: str, correction: str) -> None:
        """Callback when a rule is added via hotkey."""
        logger.info(f"Rule added via hotkey: {typo} -> {correction}")

    try:
        _hotkey = AddRuleHotkey(on_rule_added=on_rule_added)
        _hotkey.register()
        print("Hotkey active: Win+Shift+A to add new rules")
    except ImportError as e:
        print(f"Warning: Hotkey unavailable: {e}")
        _hotkey = None

    print()
    print("Monitoring keystrokes...")
    print("Corrections are now ACTIVE - typos will be replaced automatically.")
    print()
    if _tray:
        print("Use the system tray icon to exit, or press Ctrl+C.")
    else:
        print("Press Ctrl+C to exit.")
    print("-" * 50)

    # Start file watcher for hot reload
    watcher = RuleFileWatcher(_matcher)
    watcher.start()

    engine = KeystrokeEngine(
        on_word_complete=on_word_detected,
        on_correction_pattern=on_correction_pattern,
    )

    try:
        engine.start()
        logger.info("Keystroke engine started successfully")

        # Wait for shutdown signal (from tray Exit or Ctrl+C)
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=1.0)

    except ImportError as e:
        print(f"\nError: {e}")
        print("\nThis application requires the 'keyboard' library.")
        print("Install it with: pip install keyboard")
        print("\nNote: On Windows, you may need to run as Administrator.")
        return 1

    except PermissionError:
        print("\nError: Permission denied for keyboard access.")
        print("On Windows, try running as Administrator.")
        print("On Linux, you may need root access or to be in the 'input' group.")
        return 1

    except KeyboardInterrupt:
        print("\n")
        logger.info("Received shutdown signal (Ctrl+C)")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    finally:
        # Clean shutdown sequence
        if _hotkey:
            _hotkey.unregister()
        if _tray:
            _tray.stop()
        watcher.stop()
        engine.stop()
        if _correction_engine:
            print(f"Total corrections made: {_correction_engine.correction_count}")
        if _pattern_tracker and _pattern_tracker.suggestion_count > 0:
            print(f"Pending suggestions: {_pattern_tracker.suggestion_count}")
            print("  Review suggestions.txt to enable new corrections")
        print("Custom Autocorrect stopped. Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
