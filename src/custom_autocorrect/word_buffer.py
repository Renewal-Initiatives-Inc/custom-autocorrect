"""Word buffer for accumulating typed characters.

This module provides the WordBuffer class that manages character accumulation
for word detection. It follows Design Principle P3 (Minimal State) by only
tracking the current word being typed.

The buffer is intentionally kept as pure Python logic with no I/O or keyboard
dependencies, making it easy to unit test.
"""

from typing import Iterator


class WordBuffer:
    """Accumulates characters to form words.

    Design Principle P3 (Minimal State): Only tracks the current word.
    Resets on every delimiter.

    The buffer uses a list internally for O(1) append/pop operations.
    """

    def __init__(self) -> None:
        """Initialize an empty word buffer."""
        self._buffer: list[str] = []

    def add_character(self, char: str) -> None:
        """Add a single character to the buffer.

        Args:
            char: A single character to append. If multiple characters are
                  passed, only the first is used.
        """
        if char:
            self._buffer.append(char[0])

    def remove_last(self) -> None:
        """Remove the last character from the buffer (backspace behavior).

        This is a no-op if the buffer is empty, following Design Principle P4
        (Fail Safe) - when uncertain, do nothing harmful.
        """
        if self._buffer:
            self._buffer.pop()

    def get_word(self) -> str:
        """Return the current buffer contents as a string.

        Returns:
            The accumulated characters joined as a single string.
        """
        return "".join(self._buffer)

    def clear(self) -> None:
        """Clear all characters from the buffer."""
        self._buffer.clear()

    def is_empty(self) -> bool:
        """Check if the buffer contains no characters.

        Returns:
            True if the buffer is empty, False otherwise.
        """
        return len(self._buffer) == 0

    def __len__(self) -> int:
        """Return the number of characters in the buffer.

        Returns:
            Character count.
        """
        return len(self._buffer)

    def __repr__(self) -> str:
        """Return a debug representation of the buffer.

        Returns:
            String showing buffer contents.
        """
        return f"WordBuffer({self.get_word()!r})"

    def __iter__(self) -> Iterator[str]:
        """Iterate over characters in the buffer.

        Yields:
            Each character in the buffer.
        """
        return iter(self._buffer)
