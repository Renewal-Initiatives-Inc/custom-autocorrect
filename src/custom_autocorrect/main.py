"""Main entry point for Custom Autocorrect.

Phase 3: Captures keystrokes, matches words against rules, logs potential corrections.

This module provides the application entry point that will be expanded
in later phases to include:
- Correction engine (Phase 4)
- Correction logging (Phase 5)
- Password field protection (Phase 6)
- System tray integration (Phase 8)
"""

import logging
import sys
from typing import Optional

from .keystroke_engine import KeystrokeEngine
from .paths import ensure_app_folder, ensure_rules_file, get_rules_path
from .rules import RuleFileWatcher, RuleMatcher, Rule

# Global matcher for the word detection callback
_matcher: Optional[RuleMatcher] = None


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

    Phase 3: Check against correction rules and log matches.
    Phase 4: Will actually perform the correction.

    Args:
        word: The completed word (without trailing space).
    """
    global _matcher

    if _matcher is None:
        return

    rule = _matcher.match(word)

    if rule:
        # Phase 3: Log that we would correct (actual correction in Phase 4)
        print(f"Would correct: '{word}' -> '{rule.correction}'")
        logging.getLogger(__name__).info(
            f"Match found: '{word}' -> '{rule.correction}' (rule: {rule.original_typo})"
        )
    else:
        # Debug logging for non-matches
        logging.getLogger(__name__).debug(f"No rule match for: '{word}'")


def main() -> int:
    """Start the Custom Autocorrect application.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    global _matcher

    # Check for debug flag
    debug = "--debug" in sys.argv or "-d" in sys.argv

    setup_logging(debug=debug)
    logger = logging.getLogger(__name__)

    print("Custom Autocorrect v0.2.0 - Phase 3")
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

    print("Monitoring keystrokes...")
    print("Type a word that matches a rule + SPACE to see it detected.")
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
        print("Custom Autocorrect stopped. Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
