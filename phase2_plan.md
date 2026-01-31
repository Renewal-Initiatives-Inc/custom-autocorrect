# Phase 2 Execution Plan: Core Keystroke Engine

## Overview

**Goal**: Build the foundation - capture keystrokes, maintain a word buffer, detect word boundaries.

**Deliverable**: Running app that prints each completed word to console when space is pressed.

**Estimated Complexity**: Medium - Core functionality with library evaluation

---

## Prerequisites (Phase 1 Verification)

Before starting Phase 2, verify these Phase 1 deliverables are complete:

- [ ] Python 3.11+ installed on Windows development machine
- [ ] Virtual environment created and activated
- [ ] Git configured and repository cloned
- [ ] Basic project structure exists
- [ ] Can run Python scripts and push to GitHub

**Verification Command**:
```bash
python --version  # Should show 3.11+
pip list          # Should show virtual environment packages
git status        # Should show clean working directory
```

---

## Project Structure

Create the following file structure for Phase 2:

```
custom-autocorrect/
├── src/
│   └── custom_autocorrect/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── keystroke_engine.py  # Keyboard hook implementation
│       └── word_buffer.py       # Buffer logic (pure Python, testable)
├── tests/
│   ├── __init__.py
│   ├── test_word_buffer.py      # Unit tests for buffer
│   └── conftest.py              # pytest fixtures
├── requirements.txt             # Dependencies
├── requirements-dev.txt         # Development dependencies
└── pyproject.toml               # Project configuration
```

---

## Task Breakdown

### Task 2.1: Library Evaluation (keyboard vs pynput)

**Objective**: Choose the best library for system-wide keystroke capture.

**Evaluation Criteria**:
| Criterion | keyboard | pynput |
|-----------|----------|--------|
| Admin requirement | Usually requires admin | Usually requires admin |
| Ease of use | Simple API | More verbose API |
| Key suppression | Yes (can block keys) | Yes |
| Unicode support | Good | Good |
| Active maintenance | Check GitHub | Check GitHub |
| Windows support | Excellent | Excellent |

**Actions**:
1. Create a test script for each library
2. Test capturing regular keys (a-z, 0-9)
3. Test capturing special keys (space, backspace, enter, shift)
4. Test that it works in other applications (Notepad, Chrome)
5. Document findings and choose one

**Test Script Template** (`evaluate_keyboard.py`):
```python
# Test script to evaluate keyboard library
import keyboard

def on_key(event):
    print(f"Key: {event.name}, Type: {event.event_type}")

keyboard.hook(on_key)
print("Press keys to test. Press ESC to exit.")
keyboard.wait('esc')
```

**Decision Output**: Update `technology_decisions.md` with the chosen library and rationale.

---

### Task 2.2: Set Up Project Dependencies

**Objective**: Configure Python project with required packages.

**Files to Create/Modify**:

**`requirements.txt`**:
```
keyboard>=0.13.5    # Or pynput>=1.7.6 based on evaluation
```

**`requirements-dev.txt`**:
```
-r requirements.txt
pytest>=7.0.0
pytest-cov>=4.0.0
hypothesis>=6.0.0
```

**`pyproject.toml`**:
```toml
[project]
name = "custom-autocorrect"
version = "0.1.0"
description = "Silent typo correction for Windows"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

**Actions**:
1. Create the files above
2. Run `pip install -r requirements-dev.txt`
3. Verify pytest runs: `pytest --collect-only`

---

### Task 2.3: Implement Word Buffer (Pure Logic)

**Objective**: Create a testable word buffer class that manages character accumulation.

**File**: `src/custom_autocorrect/word_buffer.py`

**Class Design**:
```python
class WordBuffer:
    """
    Accumulates characters to form words.

    Design Principle P3 (Minimal State): Only tracks the current word.
    Resets on every delimiter.
    """

    def __init__(self):
        self._buffer: list[str] = []

    def add_character(self, char: str) -> None:
        """Add a single character to the buffer."""
        pass

    def remove_last(self) -> None:
        """Remove the last character (backspace behavior)."""
        pass

    def get_word(self) -> str:
        """Return the current word as a string."""
        pass

    def clear(self) -> None:
        """Clear the buffer completely."""
        pass

    def is_empty(self) -> bool:
        """Check if buffer has no characters."""
        pass

    def __len__(self) -> int:
        """Return number of characters in buffer."""
        pass
```

**Implementation Notes**:
- Use a list internally for O(1) append/pop operations
- `add_character` should only accept single characters
- `remove_last` on empty buffer should be a no-op (fail safe - P4)
- Keep this class pure (no I/O, no keyboard hooks) for easy testing

---

### Task 2.4: Implement Keystroke Engine

**Objective**: Create the keyboard hook that feeds characters to the buffer.

**File**: `src/custom_autocorrect/keystroke_engine.py`

**Class Design**:
```python
from typing import Callable, Optional
from .word_buffer import WordBuffer

class KeystrokeEngine:
    """
    Captures keystrokes system-wide and manages word detection.

    Emits completed words when space is pressed.
    """

    # Keys that should clear the buffer (reset word detection)
    BUFFER_CLEAR_KEYS = {'enter', 'tab', 'escape', 'up', 'down', 'left', 'right'}

    def __init__(self, on_word_complete: Optional[Callable[[str], None]] = None):
        """
        Args:
            on_word_complete: Callback invoked with the word when space is pressed
        """
        self._buffer = WordBuffer()
        self._on_word_complete = on_word_complete or (lambda w: None)
        self._running = False

    def start(self) -> None:
        """Start capturing keystrokes."""
        pass

    def stop(self) -> None:
        """Stop capturing keystrokes."""
        pass

    def _on_key_event(self, event) -> None:
        """Handle a keyboard event."""
        pass

    def _handle_regular_key(self, key_name: str) -> None:
        """Handle regular character keys."""
        pass

    def _handle_space(self) -> None:
        """Handle space: extract word, invoke callback, clear buffer."""
        pass

    def _handle_backspace(self) -> None:
        """Handle backspace: remove last character from buffer."""
        pass

    def _handle_clear_key(self) -> None:
        """Handle keys that reset the buffer."""
        pass
```

**Key Behaviors**:
| Key | Action |
|-----|--------|
| a-z, A-Z, 0-9 | Add to buffer |
| space | Extract word, invoke callback, clear buffer |
| backspace | Remove last character from buffer |
| enter, tab, escape, arrows | Clear buffer (word boundary) |
| shift, ctrl, alt, etc. | Ignore (modifier keys) |

**Implementation Notes**:
- Only process `key_down` events (not `key_up`) to avoid duplicates
- Filter out modifier keys that don't produce characters
- The callback receives the word WITHOUT the trailing space

---

### Task 2.5: Create Main Entry Point

**Objective**: Create a runnable script that demonstrates the engine working.

**File**: `src/custom_autocorrect/main.py`

```python
"""
Custom Autocorrect - Phase 2 Demo

Prints each completed word to the console.
Press Ctrl+C to exit.
"""

from .keystroke_engine import KeystrokeEngine

def on_word(word: str) -> None:
    """Callback when a word is completed."""
    print(f"Word detected: '{word}'")

def main() -> None:
    print("Custom Autocorrect - Keystroke Engine Demo")
    print("Type words and press space to see them captured.")
    print("Press Ctrl+C to exit.")
    print("-" * 40)

    engine = KeystrokeEngine(on_word_complete=on_word)

    try:
        engine.start()
        # Keep the main thread alive
        import keyboard
        keyboard.wait()  # Block forever until interrupted
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        engine.stop()

if __name__ == "__main__":
    main()
```

**`src/custom_autocorrect/__init__.py`**:
```python
"""Custom Autocorrect - Silent typo correction for Windows."""

__version__ = "0.1.0"
```

---

### Task 2.6: Write Unit Tests for Word Buffer

**Objective**: Comprehensive tests for the word buffer logic.

**File**: `tests/test_word_buffer.py`

**Test Cases**:

```python
import pytest
from src.custom_autocorrect.word_buffer import WordBuffer

class TestWordBuffer:
    """Unit tests for WordBuffer class."""

    def test_empty_buffer_returns_empty_string(self):
        """New buffer should return empty string."""
        buffer = WordBuffer()
        assert buffer.get_word() == ""
        assert buffer.is_empty()
        assert len(buffer) == 0

    def test_add_single_character(self):
        """Adding one character should be retrievable."""
        buffer = WordBuffer()
        buffer.add_character('a')
        assert buffer.get_word() == "a"
        assert len(buffer) == 1

    def test_add_multiple_characters(self):
        """Characters accumulate in order."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        assert buffer.get_word() == "hello"

    def test_remove_last_character(self):
        """Backspace removes last character."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        buffer.remove_last()
        assert buffer.get_word() == "hell"

    def test_remove_last_on_empty_buffer(self):
        """Backspace on empty buffer is safe (no-op)."""
        buffer = WordBuffer()
        buffer.remove_last()  # Should not raise
        assert buffer.get_word() == ""

    def test_clear_buffer(self):
        """Clear empties the buffer."""
        buffer = WordBuffer()
        for char in "hello":
            buffer.add_character(char)
        buffer.clear()
        assert buffer.get_word() == ""
        assert buffer.is_empty()

    def test_unicode_characters(self):
        """Buffer handles unicode characters."""
        buffer = WordBuffer()
        for char in "café":
            buffer.add_character(char)
        assert buffer.get_word() == "café"

    def test_mixed_case_preserved(self):
        """Buffer preserves character casing."""
        buffer = WordBuffer()
        for char in "HeLLo":
            buffer.add_character(char)
        assert buffer.get_word() == "HeLLo"

    def test_numbers_supported(self):
        """Buffer accepts numbers."""
        buffer = WordBuffer()
        for char in "test123":
            buffer.add_character(char)
        assert buffer.get_word() == "test123"
```

**Property-Based Tests** (using Hypothesis):

```python
from hypothesis import given, strategies as st

class TestWordBufferProperties:
    """Property-based tests for WordBuffer."""

    @given(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=['L', 'N'])))
    def test_add_all_chars_recovers_original(self, text):
        """Adding all chars of a string should recover that string."""
        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)
        assert buffer.get_word() == text

    @given(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=['L', 'N'])))
    def test_remove_all_chars_empties_buffer(self, text):
        """Removing all chars should empty the buffer."""
        buffer = WordBuffer()
        for char in text:
            buffer.add_character(char)
        for _ in text:
            buffer.remove_last()
        assert buffer.is_empty()

    @given(st.integers(min_value=0, max_value=100))
    def test_extra_removes_are_safe(self, extra_removes):
        """Removing more chars than exist should be safe."""
        buffer = WordBuffer()
        buffer.add_character('a')
        for _ in range(1 + extra_removes):
            buffer.remove_last()
        assert buffer.is_empty()
```

---

### Task 2.7: Manual Integration Testing

**Objective**: Verify the keystroke engine works across applications.

**Test Procedure**:

1. **Run the demo**:
   ```bash
   python -m src.custom_autocorrect.main
   ```

2. **Test in Notepad**:
   - Open Notepad
   - Type "hello " (with space)
   - Verify console shows: `Word detected: 'hello'`

3. **Test in Chrome**:
   - Open Chrome, go to any text input
   - Type "world " (with space)
   - Verify console shows: `Word detected: 'world'`

4. **Test backspace handling**:
   - Type "helllo"
   - Press backspace twice
   - Type "o "
   - Verify console shows: `Word detected: 'hello'`

5. **Test buffer clear keys**:
   - Type "partial"
   - Press Enter
   - Type "newword "
   - Verify console shows: `Word detected: 'newword'` (not "partialnewword")

6. **Test special characters**:
   - Type "café " (if keyboard supports)
   - Verify word is captured correctly

**Expected Results Checklist**:
- [ ] Words captured in Notepad
- [ ] Words captured in Chrome text fields
- [ ] Backspace correctly removes characters
- [ ] Enter/Tab/Escape clears the buffer
- [ ] Arrow keys clear the buffer
- [ ] Shift/Ctrl alone don't add characters
- [ ] Capital letters work (Shift+letter)

---

## Acceptance Criteria Mapping

| Requirement | Criteria | Phase 2 Coverage |
|-------------|----------|------------------|
| REQ-1 | 1. Monitor keystrokes system-wide | ✅ Full |
| REQ-1 | 3. Detect word + space | ✅ Full |
| REQ-1 | 5. Whole-word matching | ⏳ Foundation (buffer provides words) |

**Note**: Phase 2 provides the foundation for REQ-1. The actual correction logic (criteria 2, 4, 6, 7, 8) comes in Phases 3-4.

---

## Definition of Done

Phase 2 is complete when:

- [ ] Library evaluation documented in `technology_decisions.md`
- [ ] `WordBuffer` class implemented with all methods
- [ ] `KeystrokeEngine` class captures keystrokes and emits words
- [ ] Main script runs and prints words to console
- [ ] All unit tests pass (`pytest tests/`)
- [ ] Manual testing verifies words captured in Notepad and Chrome
- [ ] Backspace handling works correctly
- [ ] Buffer-clearing keys (Enter, Tab, Escape, arrows) work correctly
- [ ] Code committed and pushed to GitHub

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Admin rights required | Document requirement; test behavior without admin |
| Library doesn't capture in all apps | Test across multiple applications early |
| Key repeat events cause duplicates | Filter to only `key_down` events |
| Unicode/special character issues | Test with extended characters early |

---

## Files Created/Modified Summary

| File | Action | Purpose |
|------|--------|---------|
| `requirements.txt` | Create | Runtime dependencies |
| `requirements-dev.txt` | Create | Development dependencies |
| `pyproject.toml` | Create | Project configuration |
| `src/custom_autocorrect/__init__.py` | Create | Package init |
| `src/custom_autocorrect/word_buffer.py` | Create | Buffer logic |
| `src/custom_autocorrect/keystroke_engine.py` | Create | Keyboard hook |
| `src/custom_autocorrect/main.py` | Create | Entry point |
| `tests/__init__.py` | Create | Test package init |
| `tests/conftest.py` | Create | pytest fixtures |
| `tests/test_word_buffer.py` | Create | Buffer unit tests |
| `technology_decisions.md` | Modify | Add keyboard library decision |

---

## Next Phase Preview

Phase 3 (Rule Loading & Matching) will build on this foundation:
- Load `rules.txt` and parse typo→correction mappings
- Match completed words against rules
- Log "Would correct X → Y" messages
- This phase's `KeystrokeEngine` will be extended with a rule matcher callback
