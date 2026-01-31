# Phase 5: Correction Logging - Execution Plan

## Overview

**Goal**: Log corrections to a rolling log file for verification.

**Deliverable**: Each correction is logged to `Documents/CustomAutocorrect/corrections.log`.

**Satisfies Requirements**: REQ-6 (Correction Logging)

---

## Phase Dependencies Verification

Before starting Phase 5, verify these Phase 4 deliverables are working:

- [ ] `CorrectionEngine.correct()` returns success/failure boolean
- [ ] `on_word_detected()` in main.py has access to original word and correction
- [ ] `get_corrections_log_path()` in paths.py returns correct path
- [ ] `ensure_app_folder()` creates Documents/CustomAutocorrect if needed

---

## Tasks

### Task 1: Implement Active Window Title Detection

**File**: `src/custom_autocorrect/logging.py`

**Description**: Detect the currently focused window's title for log context.

**Implementation Details**:
- Use Windows API (`ctypes` with `user32.dll`) to get foreground window
- `GetForegroundWindow()` → window handle
- `GetWindowTextW()` → window title string
- Return "Unknown" if detection fails (fail-safe principle)

**Functions to implement**:
```python
def get_active_window_title() -> str:
    """Get the title of the currently active/foreground window.

    Returns:
        Window title string, or "Unknown" if detection fails.
    """
```

**Edge cases**:
- Window has no title → return "Unknown"
- No window focused → return "Unknown"
- Non-Windows platform → return "Unknown" (graceful fallback)
- Win32 API call fails → return "Unknown"

---

### Task 2: Implement Log Entry Formatting

**File**: `src/custom_autocorrect/logging.py`

**Description**: Format correction entries according to spec.

**Format**: `2026-01-31 14:23:15 | teh → the | Chrome - Google Docs`

**Functions to implement**:
```python
def format_log_entry(original: str, corrected: str, window_title: str) -> str:
    """Format a correction as a log entry string.

    Args:
        original: The typo as typed (with original casing).
        corrected: The corrected text (with applied casing).
        window_title: Title of the active window.

    Returns:
        Formatted log entry string with timestamp.
    """
```

**Details**:
- Timestamp format: `%Y-%m-%d %H:%M:%S` (ISO-like, human-readable)
- Arrow: `→` (Unicode arrow for readability)
- Separator: ` | ` (pipe with spaces)

---

### Task 3: Implement Log Rotation

**File**: `src/custom_autocorrect/logging.py`

**Description**: Maintain max 100 entries using oldest-first removal.

**Functions to implement**:
```python
MAX_LOG_ENTRIES = 100

def read_log_entries(log_path: Path) -> list[str]:
    """Read existing log entries from file.

    Returns:
        List of log entry strings (may be empty).
    """

def write_log_entries(log_path: Path, entries: list[str]) -> bool:
    """Write log entries to file.

    Returns:
        True if successful, False on error.
    """

def rotate_log(entries: list[str], max_entries: int = MAX_LOG_ENTRIES) -> list[str]:
    """Remove oldest entries if list exceeds max size.

    Args:
        entries: Current log entries.
        max_entries: Maximum allowed entries.

    Returns:
        Rotated list with at most max_entries items.
    """
```

**Algorithm**:
1. Read existing entries
2. Append new entry
3. If count > 100, remove oldest (first) entries
4. Write back to file

---

### Task 4: Implement Main Logging Function

**File**: `src/custom_autocorrect/logging.py`

**Description**: Public function that combines all logging logic.

**Functions to implement**:
```python
def log_correction(original: str, corrected: str) -> bool:
    """Log a correction to the rolling log file.

    Captures active window, formats entry, handles rotation.

    Args:
        original: The typo as typed.
        corrected: The corrected text.

    Returns:
        True if logged successfully, False on error.
    """
```

**Behavior**:
1. Get active window title
2. Format log entry
3. Read existing log (or empty list if missing/error)
4. Append new entry
5. Rotate if needed
6. Write log file
7. Return success/failure

---

### Task 5: Handle Edge Cases

**File**: `src/custom_autocorrect/logging.py`

**Edge cases to handle**:

| Case | Behavior |
|------|----------|
| Log file doesn't exist | Create it with first entry |
| Log file is empty | Start fresh with first entry |
| Log file is locked (another process) | Retry once after brief delay, then skip |
| Log file has invalid content | Treat as empty, overwrite |
| No write permission | Return False, app continues without logging |
| Window title is empty | Use "Unknown" |
| Window detection fails | Use "Unknown" |
| Disk full | Return False, app continues |

**Error handling pattern**:
- Log errors via Python logging module
- Never raise exceptions from logging functions
- Always return True/False to indicate success
- Follow fail-safe principle: app works even if logging fails

---

### Task 6: Integrate with Correction Engine

**File**: `src/custom_autocorrect/main.py`

**Changes to `on_word_detected()`**:

```python
# After successful correction (line 57-63):
if success:
    # Phase 5: Log the correction
    from .logging import log_correction
    log_correction(word, applied_correction)

    logging.getLogger(__name__).info(...)
```

**Note**: Need to get the cased correction, not just `rule.correction`. The casing is applied inside `CorrectionEngine.correct()`, so we need to either:
- Option A: Have `correct()` return the applied correction string
- Option B: Re-apply casing in `on_word_detected()` before logging

**Recommended**: Option A - modify `correct()` to return `tuple[bool, Optional[str]]` with (success, applied_correction).

---

### Task 7: Write Unit Tests for Log Formatting

**File**: `tests/test_logging.py`

**Test cases**:
```python
class TestFormatLogEntry:
    def test_basic_format(self):
        """Entry has correct format with all parts."""

    def test_timestamp_format(self):
        """Timestamp matches expected format."""

    def test_unicode_arrow(self):
        """Uses → character for arrow."""

    def test_preserves_casing(self):
        """Original and corrected preserve their casing."""

    def test_unknown_window(self):
        """Handles 'Unknown' window title."""

    def test_long_window_title(self):
        """Long window titles work without truncation."""
```

---

### Task 8: Write Unit Tests for Log Rotation

**File**: `tests/test_logging.py`

**Test cases**:
```python
class TestRotateLog:
    def test_under_limit_unchanged(self):
        """Entries under limit are not modified."""

    def test_at_limit_unchanged(self):
        """Exactly 100 entries are not modified."""

    def test_over_limit_removes_oldest(self):
        """101 entries removes first, keeps last 100."""

    def test_empty_list(self):
        """Empty list returns empty list."""

    def test_way_over_limit(self):
        """200 entries trims to exactly 100."""

    def test_preserves_order(self):
        """Kept entries maintain their order."""
```

---

### Task 9: Write Unit Tests for File Operations

**File**: `tests/test_logging.py`

**Test cases**:
```python
class TestLogFile:
    def test_creates_file_if_missing(self, tmp_path):
        """First log creates the file."""

    def test_appends_to_existing(self, tmp_path):
        """New entries append to existing log."""

    def test_handles_locked_file(self, tmp_path):
        """Returns False if file is locked."""

    def test_handles_permission_error(self, tmp_path):
        """Returns False on permission denied."""

    def test_handles_corrupted_file(self, tmp_path):
        """Corrupted file is replaced."""

    def test_utf8_encoding(self, tmp_path):
        """File uses UTF-8 encoding."""
```

---

### Task 10: Write Property-Based Tests (CP5)

**File**: `tests/test_properties.py` (add to existing)

**Property**: CP5 - Log Rotation - **For any** state of corrections.log, **the file shall contain at most 100 entries**.

```python
from hypothesis import given, strategies as st

class TestLogRotationProperty:
    @given(st.integers(min_value=0, max_value=500))
    def test_rotation_never_exceeds_max(self, num_entries):
        """Log rotation always produces <= MAX_LOG_ENTRIES."""
        entries = [f"entry_{i}" for i in range(num_entries)]
        rotated = rotate_log(entries)
        assert len(rotated) <= MAX_LOG_ENTRIES

    @given(st.lists(st.text(min_size=1), min_size=0, max_size=300))
    def test_rotation_preserves_newest(self, entries):
        """Rotation keeps the newest entries."""
        rotated = rotate_log(entries)
        if len(entries) > MAX_LOG_ENTRIES:
            assert rotated == entries[-MAX_LOG_ENTRIES:]

    @given(st.integers(min_value=101, max_value=500))
    def test_large_sequences_handled(self, num_corrections):
        """Simulating many corrections keeps log bounded."""
        # Simulate num_corrections being logged
        entries = []
        for i in range(num_corrections):
            entries.append(f"2026-01-31 00:00:{i:02d} | typo{i} → fix{i} | Window")
            entries = rotate_log(entries)

        assert len(entries) <= MAX_LOG_ENTRIES
```

---

### Task 11: Write Integration Tests

**File**: `tests/test_logging.py`

**Test cases**:
```python
class TestLoggingIntegration:
    def test_full_logging_flow(self, tmp_path, monkeypatch):
        """Full flow: correction → log entry appears in file."""

    def test_window_title_captured(self, tmp_path, mock_window):
        """Active window title is included in log."""

    def test_rotation_during_session(self, tmp_path):
        """Logging 150 corrections results in 100 entries."""
```

---

### Task 12: Update Module Exports

**File**: `src/custom_autocorrect/__init__.py`

Add exports for new functions:
```python
from .logging import log_correction, get_active_window_title
```

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/custom_autocorrect/logging.py` | Replace | Full implementation (currently placeholder) |
| `src/custom_autocorrect/main.py` | Modify | Add logging call in `on_word_detected()` |
| `src/custom_autocorrect/__init__.py` | Modify | Export new functions |
| `tests/test_logging.py` | Create | Unit tests for logging module |
| `tests/test_properties.py` | Modify | Add CP5 property tests |

---

## Acceptance Criteria (from REQ-6)

- [ ] **AC1**: THE System SHALL log each correction to `corrections.log`
- [ ] **AC2**: THE System SHALL record: timestamp, original word, corrected word, active window title
- [ ] **AC3**: THE System SHALL maintain a maximum of 100 log entries
- [ ] **AC4**: THE System SHALL rotate out oldest entries when the limit is reached
- [ ] **AC5**: THE System SHALL store the log in `Documents/CustomAutocorrect/`

---

## Correctness Property (from design.md)

**CP5: Log Rotation**
> **For any** state of corrections.log, **the file shall contain at most 100 entries**.

This will be verified by property-based tests that simulate logging sequences of 200+ corrections.

---

## Implementation Order

1. **Task 1**: Active window detection (can be tested standalone)
2. **Task 2**: Log entry formatting (pure function, easy to test)
3. **Task 3**: Log rotation logic (pure function, easy to test)
4. **Task 4**: Main logging function (combines above)
5. **Task 5**: Edge case handling (built into above functions)
6. **Tasks 7-10**: Write tests (parallel with implementation)
7. **Task 6**: Integration with main.py (last, after logging works)
8. **Task 12**: Update exports

---

## Testing Checklist

### Automated Tests
- [ ] All unit tests pass for log formatting
- [ ] All unit tests pass for log rotation
- [ ] All unit tests pass for file operations
- [ ] Property tests pass (CP5)
- [ ] Integration tests pass

### Manual Testing
- [ ] Type typo in Notepad, verify log entry appears
- [ ] Type typo in Chrome, verify window title captured
- [ ] Log 105+ corrections, verify only 100 remain
- [ ] Close and reopen app, verify log persists
- [ ] Verify log file readable in text editor

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Window detection fails on some apps | Return "Unknown", test across apps |
| File locking during rotation | Retry with short delay, skip on failure |
| High frequency corrections | Batch writes if needed (future optimization) |
| Performance impact | Profile; logging is I/O so should be fast |

---

## Notes for Implementation

1. **Naming conflict**: The module is named `logging.py` but Python has a built-in `logging` module. Consider renaming to `correction_log.py` to avoid import confusion.

2. **Return value from correct()**: Currently returns `bool`. For logging, we need the cased correction string. Consider:
   - Adding a new method `correct_and_get()` that returns both
   - Or storing last correction as an attribute

3. **Thread safety**: If keystroke handling is in a different thread, ensure log writes are thread-safe (use file locking or queue).

4. **Encoding**: Always use UTF-8 for log file (arrow character `→` requires it).
