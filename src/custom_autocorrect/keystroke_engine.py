"""Keystroke monitoring and word buffer management.

This module provides the KeystrokeEngine class that:
- Captures keystrokes system-wide using the keyboard library
- Maintains a word buffer that accumulates characters
- Detects word boundaries when space is pressed
- Handles backspace and special keys appropriately
- Detects correction patterns (Phase 7): when user erases a word and types a replacement

Phase 2 Implementation for Custom Autocorrect.
Phase 7: Added correction pattern detection via backspace tracking.
"""

import logging
from typing import Callable, Optional, Set

from .word_buffer import WordBuffer

logger = logging.getLogger(__name__)


class KeystrokeEngine:
    """Captures keystrokes system-wide and manages word detection.

    Emits completed words when space is pressed. The engine uses a callback
    pattern to notify listeners when a word is completed.

    Phase 7: Also detects correction patterns. When a user erases a complete
    word via backspace and types a different word, this triggers the
    on_correction_pattern callback with (erased_word, replacement_word).

    Attributes:
        BUFFER_CLEAR_KEYS: Set of key names that clear the word buffer.
        MODIFIER_KEYS: Set of modifier key names to ignore.
    """

    BUFFER_CLEAR_KEYS: Set[str] = {
        "enter",
        "tab",
        "escape",
        "up",
        "down",
        "left",
        "right",
        "home",
        "end",
        "page up",
        "page down",
        "insert",
        "delete",
    }

    MODIFIER_KEYS: Set[str] = {
        "shift",
        "ctrl",
        "alt",
        "left shift",
        "right shift",
        "left ctrl",
        "right ctrl",
        "left alt",
        "right alt",
        "left windows",
        "right windows",
        "caps lock",
        "num lock",
        "scroll lock",
    }

    def __init__(
        self,
        on_word_complete: Optional[Callable[[str], None]] = None,
        on_correction_pattern: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        """Initialize the keystroke engine.

        Args:
            on_word_complete: Callback invoked with the word when space is pressed.
                              The word does NOT include the trailing space.
            on_correction_pattern: Callback invoked when a correction pattern is
                              detected, i.e., when user erases a word via backspace
                              and types a different word. Called with (erased, replacement).
        """
        self._buffer = WordBuffer()
        self._on_word_complete = on_word_complete or (lambda w: None)
        self._on_correction_pattern = on_correction_pattern
        self._running = False
        self._hook = None
        # Phase 7: Track word that was erased by backspaces
        self._erased_word: str = ""
        self._fully_erased: bool = False  # True only when buffer was completely emptied

    @property
    def buffer(self) -> WordBuffer:
        """Access the internal word buffer (for testing)."""
        return self._buffer

    @property
    def is_running(self) -> bool:
        """Check if the engine is currently capturing keystrokes."""
        return self._running

    def start(self) -> None:
        """Start capturing keystrokes.

        Raises:
            RuntimeError: If the engine is already running.
            ImportError: If the keyboard library is not available.
        """
        if self._running:
            raise RuntimeError("KeystrokeEngine is already running")

        try:
            import keyboard
        except ImportError as e:
            raise ImportError(
                "The 'keyboard' library is required for keystroke capture. "
                "Install it with: pip install keyboard"
            ) from e

        logger.info("Starting keystroke capture")
        self._hook = keyboard.hook(self._on_key_event, suppress=False)
        self._running = True

    def stop(self) -> None:
        """Stop capturing keystrokes."""
        if not self._running:
            return

        try:
            import keyboard

            if self._hook is not None:
                keyboard.unhook(self._hook)
                self._hook = None
        except Exception as e:
            logger.warning(f"Error unhooking keyboard: {e}")

        self._running = False
        self._buffer.clear()
        # Phase 7: Clear erased word tracking
        self._erased_word = ""
        self._fully_erased = False
        logger.info("Stopped keystroke capture")

    def _on_key_event(self, event) -> None:
        """Handle a keyboard event from the keyboard library.

        Args:
            event: A keyboard.KeyboardEvent with name and event_type attributes.
        """
        # Only process key down events to avoid duplicates
        if event.event_type != "down":
            return

        key_name = event.name.lower() if event.name else ""

        # Ignore modifier keys (they don't produce characters)
        if key_name in self.MODIFIER_KEYS:
            return

        # Handle special keys
        if key_name == "space":
            self._handle_space()
        elif key_name == "backspace":
            self._handle_backspace()
        elif key_name in self.BUFFER_CLEAR_KEYS:
            self._handle_clear_key()
        else:
            self._handle_regular_key(event.name)

    def _handle_regular_key(self, key_name: str) -> None:
        """Handle regular character keys.

        Args:
            key_name: The name of the key pressed. For regular keys, this is
                      the character itself (preserving case).
        """
        # The keyboard library provides the actual character (with shift applied)
        # Only add single-character keys (letters, numbers, some punctuation)
        if key_name and len(key_name) == 1:
            self._buffer.add_character(key_name)
            logger.debug(f"Buffer: {self._buffer.get_word()!r}")

    def _handle_space(self) -> None:
        """Handle space key: extract word, invoke callback, clear buffer.

        Phase 7: Also checks for correction pattern - if there was an erased word
        that was FULLY deleted (buffer emptied) and the new word is different,
        trigger the correction pattern callback.
        """
        word = self._buffer.get_word()
        self._buffer.clear()

        if word:
            # Phase 7: Check for correction pattern before word complete callback
            # Only trigger if word was FULLY erased (not just partially backspaced)
            if (self._fully_erased and self._erased_word and
                    self._erased_word.lower() != word.lower()):
                if self._on_correction_pattern:
                    try:
                        self._on_correction_pattern(self._erased_word, word)
                    except Exception as e:
                        logger.error(f"Error in correction pattern callback: {e}")

            # Clear erased word tracking after processing
            self._erased_word = ""
            self._fully_erased = False

            logger.debug(f"Word completed: {word!r}")
            try:
                self._on_word_complete(word)
            except Exception as e:
                logger.error(f"Error in word complete callback: {e}")

    def _handle_backspace(self) -> None:
        """Handle backspace: remove last character from buffer.

        Phase 7: Track the word being erased. When user starts erasing (first
        backspace on a non-empty buffer with no prior erased word), save the
        current word. When buffer becomes empty, mark as fully erased.
        """
        # Phase 7: Capture the word when erasing STARTS (not when it ends)
        # Only save if we haven't already started tracking an erase sequence
        if not self._erased_word and not self._buffer.is_empty():
            self._erased_word = self._buffer.get_word()
            logger.debug(f"Started erasing word: {self._erased_word!r}")

        self._buffer.remove_last()

        # Phase 7: Mark as fully erased when buffer becomes empty
        if self._buffer.is_empty() and self._erased_word:
            self._fully_erased = True
            logger.debug(f"Word fully erased: {self._erased_word!r}")

        logger.debug(f"Backspace - Buffer: {self._buffer.get_word()!r}")

    def _handle_clear_key(self) -> None:
        """Handle keys that reset the buffer (word boundary).

        Phase 7: Also clears erased word tracking since the user is navigating
        away from the current context.
        """
        if not self._buffer.is_empty():
            logger.debug(f"Buffer cleared (was: {self._buffer.get_word()!r})")
            self._buffer.clear()
        # Phase 7: Clear erased word tracking on clear keys
        self._erased_word = ""
        self._fully_erased = False

    def simulate_key(self, key_name: str, event_type: str = "down") -> None:
        """Simulate a key event for testing purposes.

        This method allows testing the engine without actual keyboard input.

        Args:
            key_name: The name of the key to simulate.
            event_type: Either "down" or "up".
        """

        class FakeEvent:
            def __init__(self, name: str, evt_type: str):
                self.name = name
                self.event_type = evt_type

        self._on_key_event(FakeEvent(key_name, event_type))
