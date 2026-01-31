"""Keystroke monitoring and word buffer management.

This module provides the KeystrokeEngine class that:
- Captures keystrokes system-wide using the keyboard library
- Maintains a word buffer that accumulates characters
- Detects word boundaries when space is pressed
- Handles backspace and special keys appropriately

Phase 2 Implementation for Custom Autocorrect.
"""

import logging
from typing import Callable, Optional, Set

from .word_buffer import WordBuffer

logger = logging.getLogger(__name__)


class KeystrokeEngine:
    """Captures keystrokes system-wide and manages word detection.

    Emits completed words when space is pressed. The engine uses a callback
    pattern to notify listeners when a word is completed.

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
        self, on_word_complete: Optional[Callable[[str], None]] = None
    ) -> None:
        """Initialize the keystroke engine.

        Args:
            on_word_complete: Callback invoked with the word when space is pressed.
                              The word does NOT include the trailing space.
        """
        self._buffer = WordBuffer()
        self._on_word_complete = on_word_complete or (lambda w: None)
        self._running = False
        self._hook = None

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
        """Handle space key: extract word, invoke callback, clear buffer."""
        word = self._buffer.get_word()
        self._buffer.clear()

        if word:
            logger.debug(f"Word completed: {word!r}")
            try:
                self._on_word_complete(word)
            except Exception as e:
                logger.error(f"Error in word complete callback: {e}")

    def _handle_backspace(self) -> None:
        """Handle backspace: remove last character from buffer."""
        self._buffer.remove_last()
        logger.debug(f"Backspace - Buffer: {self._buffer.get_word()!r}")

    def _handle_clear_key(self) -> None:
        """Handle keys that reset the buffer (word boundary)."""
        if not self._buffer.is_empty():
            logger.debug(f"Buffer cleared (was: {self._buffer.get_word()!r})")
            self._buffer.clear()

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
