"""Main entry point for Custom Autocorrect.

Phase 2 Demo: Captures keystrokes and prints completed words to console.

This module provides the application entry point that will be expanded
in later phases to include:
- Rule loading and matching (Phase 3)
- Correction engine (Phase 4)
- Correction logging (Phase 5)
- Password field protection (Phase 6)
- System tray integration (Phase 8)
"""

import logging
import sys

from .keystroke_engine import KeystrokeEngine


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

    In Phase 2, this just prints the word. In later phases, this will:
    - Check against correction rules (Phase 3)
    - Apply corrections (Phase 4)
    - Track for suggestions (Phase 7)

    Args:
        word: The completed word (without trailing space).
    """
    print(f"Word detected: '{word}'")


def main() -> int:
    """Start the Custom Autocorrect application.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    # Check for debug flag
    debug = "--debug" in sys.argv or "-d" in sys.argv

    setup_logging(debug=debug)
    logger = logging.getLogger(__name__)

    print("Custom Autocorrect v0.1.0 - Phase 2 Demo")
    print("=" * 50)
    print()
    print("This demo captures keystrokes and prints completed words.")
    print("Type words in any application and press SPACE to see them here.")
    print()
    print("Keys handled:")
    print("  - Letters/numbers: Added to word buffer")
    print("  - Space: Completes word and prints it")
    print("  - Backspace: Removes last character")
    print("  - Enter/Tab/Escape/Arrows: Clears buffer")
    print()
    print("Press Ctrl+C to exit.")
    print("-" * 50)

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
        engine.stop()
        print("Custom Autocorrect stopped. Goodbye!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
