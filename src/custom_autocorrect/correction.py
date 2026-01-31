"""Correction engine - performs the actual text replacement.

Phase 4 Implementation:
- Casing detection and preservation
- Keyboard simulation (backspace x word length, type correction, type space)

Casing preservation logic:
  - lowercase -> lowercase
  - Capitalized -> Capitalized
  - UPPERCASE -> UPPERCASE
  - mixed -> correction as-is (safe fallback)
"""

import logging
import time
from typing import Literal

# Import keyboard at module level for easier mocking in tests
try:
    import keyboard
except ImportError:
    keyboard = None  # type: ignore

logger = logging.getLogger(__name__)

# Type alias for casing patterns
CasingPattern = Literal["lowercase", "capitalized", "uppercase", "mixed"]


def detect_casing_pattern(word: str) -> CasingPattern:
    """Detect the casing pattern of a word.

    Args:
        word: The word to analyze.

    Returns:
        "lowercase" - all lowercase (e.g., "teh")
        "capitalized" - first letter uppercase, rest lowercase (e.g., "Teh")
        "uppercase" - all uppercase (e.g., "TEH")
        "mixed" - any other pattern (e.g., "tEh", "TeTe")
    """
    if not word:
        return "lowercase"

    # Filter to just alphabetic characters for casing analysis
    alpha_chars = [c for c in word if c.isalpha()]

    if not alpha_chars:
        # No alphabetic characters (e.g., "123") - treat as lowercase
        return "lowercase"

    if all(c.islower() for c in alpha_chars):
        return "lowercase"

    if all(c.isupper() for c in alpha_chars):
        return "uppercase"

    # Check for capitalized: first alpha is upper, rest are lower
    first_alpha_idx = next(i for i, c in enumerate(word) if c.isalpha())
    first_alpha = word[first_alpha_idx]
    rest_alphas = [c for c in word[first_alpha_idx + 1:] if c.isalpha()]

    if first_alpha.isupper() and all(c.islower() for c in rest_alphas):
        return "capitalized"

    return "mixed"


def apply_casing(original_word: str, correction: str) -> str:
    """Apply the casing pattern from original_word to correction.

    Args:
        original_word: The typo as typed (with original casing).
        correction: The correction text to transform.

    Returns:
        The correction with the original word's casing pattern applied.

    Examples:
        apply_casing("teh", "the") -> "the"
        apply_casing("Teh", "the") -> "The"
        apply_casing("TEH", "the") -> "THE"
        apply_casing("tEh", "the") -> "the"  # mixed falls back to correction as-is
    """
    if not original_word or not correction:
        return correction

    pattern = detect_casing_pattern(original_word)

    if pattern == "lowercase":
        return correction.lower()

    if pattern == "uppercase":
        return correction.upper()

    if pattern == "capitalized":
        return correction.capitalize()

    # "mixed" pattern - use correction as-is (safe fallback per P4: Fail Safe)
    return correction


def perform_correction(typo_length: int, correction: str, delay_ms: int = 0) -> bool:
    """Perform correction via keyboard simulation.

    Algorithm:
    1. Send backspace key (typo_length + 1) times
       - +1 accounts for the space that triggered the correction
    2. Type the correction text
    3. Type a space (restore the delimiter)

    Args:
        typo_length: Number of characters in the original typo.
        correction: The corrected text to type.
        delay_ms: Delay in milliseconds between operations (default 0).

    Returns:
        True if correction was performed, False on error.

    Raises:
        Nothing - errors are caught and logged (fail safe).
    """
    if keyboard is None:
        logger.error("keyboard library not available")
        return False

    try:
        # Calculate total backspaces needed: typo + the space that triggered
        total_backspaces = typo_length + 1

        # Send backspaces to erase the typo and the space
        for _ in range(total_backspaces):
            keyboard.press_and_release("backspace")
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

        # Small delay before typing (helps with some applications)
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        # Type the correction followed by space
        keyboard.write(correction + " ")

        logger.debug(
            f"Performed correction: {total_backspaces} backspaces, "
            f"typed '{correction} '"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to perform correction: {e}")
        return False


class CorrectionEngine:
    """Performs typo corrections with casing preservation.

    Encapsulates the correction logic to separate concerns from keystroke detection.
    Provides a clean interface for performing corrections with configurable timing.
    """

    def __init__(self, delay_ms: int = 0):
        """Initialize the correction engine.

        Args:
            delay_ms: Delay in milliseconds between keyboard operations (default 0).
                     Increase if corrections appear garbled in some applications.
        """
        self._delay_ms = delay_ms
        self._correction_count = 0
        self._logger = logging.getLogger(__name__)

    @property
    def delay_ms(self) -> int:
        """Get the current delay setting in milliseconds."""
        return self._delay_ms

    @delay_ms.setter
    def delay_ms(self, value: int) -> None:
        """Set the delay between keyboard operations.

        Args:
            value: Delay in milliseconds (must be >= 0).
        """
        if value < 0:
            raise ValueError("delay_ms must be non-negative")
        self._delay_ms = value

    @property
    def correction_count(self) -> int:
        """Get the total number of corrections performed."""
        return self._correction_count

    def correct(self, original_word: str, rule_correction: str) -> bool:
        """Apply a correction with proper casing.

        This is the main entry point for performing corrections.
        It applies casing from the original word to the correction,
        then simulates the keyboard operations to replace the text.

        Args:
            original_word: The typo as typed (with original casing).
            rule_correction: The correction from the rule (stored casing).

        Returns:
            True if correction was performed successfully, False otherwise.
        """
        if not original_word or not rule_correction:
            self._logger.warning(
                f"Invalid correction request: original='{original_word}', "
                f"correction='{rule_correction}'"
            )
            return False

        # Apply casing pattern from original word to correction
        cased_correction = apply_casing(original_word, rule_correction)

        self._logger.debug(
            f"Correcting '{original_word}' -> '{cased_correction}' "
            f"(rule: {rule_correction}, pattern: {detect_casing_pattern(original_word)})"
        )

        # Perform the actual keyboard simulation
        success = perform_correction(
            typo_length=len(original_word),
            correction=cased_correction,
            delay_ms=self._delay_ms,
        )

        if success:
            self._correction_count += 1

        return success

    def reset_count(self) -> None:
        """Reset the correction counter to zero."""
        self._correction_count = 0
