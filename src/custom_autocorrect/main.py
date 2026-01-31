"""Main entry point for Custom Autocorrect.

Phase 6: Captures keystrokes, matches words against rules, performs corrections,
logs corrections to a rolling log file, and skips password fields.

This module provides the application entry point that will be expanded
in later phases to include:
- System tray integration (Phase 8)
"""

import logging
import sys
from typing import Optional

from .correction import CorrectionEngine, apply_casing
from .correction_log import log_correction
from .keystroke_engine import KeystrokeEngine
from .password_detect import is_password_field
from .paths import ensure_app_folder, ensure_rules_file, get_rules_path
from .rules import RuleFileWatcher, RuleMatcher, Rule

# Global instances for the word detection callback
_matcher: Optional[RuleMatcher] = None
_correction_engine: Optional[CorrectionEngine] = None


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
    global _matcher, _correction_engine

    # Check for debug flag
    debug = "--debug" in sys.argv or "-d" in sys.argv

    setup_logging(debug=debug)
    logger = logging.getLogger(__name__)

    print("Custom Autocorrect v0.5.0 - Phase 6")
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

    # Phase 4: Initialize correction engine
    _correction_engine = CorrectionEngine(delay_ms=0)

    print("Monitoring keystrokes...")
    print("Corrections are now ACTIVE - typos will be replaced automatically.")
    print()
    print("Press Ctrl+C to exit.")
    print("-" * 50)

    # Start file watcher for hot reload
    watcher = RuleFileWatcher(_matcher)
    watcher.start()

    engine = KeystrokeEngine(on_word_complete=on_word_detected)

    try:
        engine.start()
        logger.info("Keystroke engine started successfully")

        # Keep the main thread alive
        # The keyboard library runs its own event loop
        import keyboard

        keyboard.wait()  # Block forever until Ctrl+C

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
        logger.info("Received shutdown signal")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    finally:
        watcher.stop()
        engine.stop()
        if _correction_engine:
            print(f"Total corrections made: {_correction_engine.correction_count}")
        print("Custom Autocorrect stopped. Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
