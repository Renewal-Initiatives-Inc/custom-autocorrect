# Phase 6: Password Field Protection - Execution Plan

## Overview

**Goal**: Skip corrections in password fields to avoid breaking passwords.

**Key Principle**: P4 (Fail Safe) - When uncertain, do nothing. A missed correction is far better than a wrong one.

**Design Constraint**: This is "best-effort" detection per REQ-3. Windows UI Automation cannot detect all password fields reliably.

---

## Prerequisites Verification

Before starting Phase 6, verify these from previous phases:

- [ ] Phase 5 correction logging works (`corrections.log` being written)
- [ ] Corrections are happening via `main.py` → `on_word_detected()` flow
- [ ] Tests pass: `pytest tests/`

---

## Tasks

### Task 1: Research Windows UI Automation API

**Objective**: Understand how to detect password fields on Windows.

**Research Areas**:
1. **Windows UI Automation (UIA)** - COM-based accessibility API
   - `UIAutomation` library for Python
   - `comtypes` for direct COM access
   - Focus element retrieval via `IUIAutomation::GetFocusedElement`

2. **Password Field Indicators**:
   - `UIA_IsPasswordPatternAvailablePropertyId` - True for password controls
   - Control type: `UIA_EditControlTypeId` (50004) with password pattern
   - `UIA_ValueIsReadOnlyPropertyId` may help distinguish

3. **Alternative Libraries**:
   - `pywinauto` - Higher-level wrapper (might be overkill)
   - `uiautomation` PyPI package - Simpler Python wrapper

**Deliverable**: Choose approach (likely `comtypes` for minimal dependencies or `uiautomation` for simplicity).

---

### Task 2: Implement Password Field Detection

**File**: `src/custom_autocorrect/password_detect.py`

**Functions to Implement**:

```python
def is_password_field() -> bool:
    """
    Check if the currently focused control is a password field.

    Returns:
        True if password field detected
        False if not a password field OR detection failed (fail-safe)

    Design: Fail-safe - return False on any error so corrections continue.
    This may miss some password fields, but won't block normal operation.
    """
```

**Implementation Approach**:

1. **Using `comtypes` (recommended for minimal dependencies)**:
   ```python
   import comtypes.client
   from comtypes import GUID

   # Load UIA type library
   UIAutomationClient = comtypes.client.GetModule("UIAutomationClient.dll")

   # Get IUIAutomation instance
   uia = comtypes.CoCreateInstance(
       UIAutomationClient.CUIAutomation._reg_clsid_,
       interface=UIAutomationClient.IUIAutomation,
       clsctx=comtypes.CLSCTX_INPROC_SERVER
   )

   # Get focused element
   focused = uia.GetFocusedElement()

   # Check if password pattern is available
   is_password = focused.GetCurrentPropertyValue(
       UIAutomationClient.UIA_IsPasswordPatternAvailablePropertyId
   )
   ```

2. **Using `uiautomation` package (simpler but adds dependency)**:
   ```python
   import uiautomation as auto

   focused = auto.GetFocusedControl()
   if focused and hasattr(focused, 'IsPassword'):
       return focused.IsPassword
   ```

**Error Handling**:
- Wrap in try/except - any exception returns `False` (fail-safe)
- Log errors at DEBUG level (don't spam logs)
- Cache result briefly to avoid repeated COM calls (optional optimization)

**Module Exports**: Update `__init__.py` to export `is_password_field`.

---

### Task 3: Integrate with Correction Flow

**File**: `src/custom_autocorrect/main.py`

**Modification**: Add password field check before performing corrections.

**Current Flow** (simplified):
```python
def on_word_detected(word: str) -> None:
    rule = rule_matcher.match(word)
    if rule:
        # Perform correction
        cased_correction = apply_casing(word, rule.correction)
        if correction_engine.correct(word, cased_correction):
            log_correction(word, cased_correction)
```

**Updated Flow**:
```python
from custom_autocorrect.password_detect import is_password_field

def on_word_detected(word: str) -> None:
    # CP7: Password Field Safety - skip corrections in password fields
    if is_password_field():
        logging.debug(f"Skipped correction in password field: {word}")
        return

    rule = rule_matcher.match(word)
    if rule:
        # Perform correction
        cased_correction = apply_casing(word, rule.correction)
        if correction_engine.correct(word, cased_correction):
            log_correction(word, cased_correction)
```

**Design Decision**: Check at word detection time (not per-keystroke) for efficiency.

---

### Task 4: Write Unit Tests

**File**: `tests/test_password_detect.py`

**Test Cases**:

1. **Basic Functionality**:
   ```python
   def test_is_password_field_returns_bool():
       """Function should always return a boolean."""
       result = is_password_field()
       assert isinstance(result, bool)
   ```

2. **Fail-Safe on Import Error** (mock missing comtypes):
   ```python
   def test_returns_false_when_comtypes_unavailable():
       """Should return False (fail-safe) if COM library unavailable."""
       # Mock the import to fail
       with patch.dict('sys.modules', {'comtypes': None}):
           # Reload module or test fallback behavior
           assert is_password_field() == False
   ```

3. **Fail-Safe on Exception**:
   ```python
   def test_returns_false_on_exception():
       """Any exception should return False (fail-safe)."""
       with patch('custom_autocorrect.password_detect._get_focused_element') as mock:
           mock.side_effect = Exception("COM error")
           assert is_password_field() == False
   ```

4. **Password Field Detection** (with mocked UIA):
   ```python
   def test_detects_password_field():
       """Should return True when focused element is password field."""
       with patch('...') as mock_uia:
           mock_uia.GetFocusedElement.return_value.GetCurrentPropertyValue.return_value = True
           assert is_password_field() == True

   def test_non_password_field():
       """Should return False for regular text fields."""
       with patch('...') as mock_uia:
           mock_uia.GetFocusedElement.return_value.GetCurrentPropertyValue.return_value = False
           assert is_password_field() == False
   ```

5. **No Focused Element**:
   ```python
   def test_returns_false_when_no_focused_element():
       """Should return False if no element is focused."""
       with patch('...') as mock_uia:
           mock_uia.GetFocusedElement.return_value = None
           assert is_password_field() == False
   ```

---

### Task 5: Write Integration Tests

**File**: `tests/test_password_detect.py` (or separate integration file)

**Integration Test with Main Flow**:

```python
def test_correction_skipped_in_password_field():
    """Corrections should be skipped when password field is detected."""
    with patch('custom_autocorrect.main.is_password_field', return_value=True):
        with patch('custom_autocorrect.main.correction_engine.correct') as mock_correct:
            # Simulate word detection
            on_word_detected("teh")
            # Correction should NOT have been called
            mock_correct.assert_not_called()

def test_correction_applied_in_normal_field():
    """Corrections should work normally in non-password fields."""
    with patch('custom_autocorrect.main.is_password_field', return_value=False):
        with patch('custom_autocorrect.main.correction_engine.correct') as mock_correct:
            mock_correct.return_value = True
            # Setup rule matcher to return a rule
            # Simulate word detection
            on_word_detected("teh")
            # Correction SHOULD have been called
            mock_correct.assert_called_once()
```

---

### Task 6: Add Property-Based Test for CP7

**File**: `tests/test_properties.py`

**Property Test**:

```python
from hypothesis import given, strategies as st

@given(word=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L',))))
def test_cp7_password_field_safety(word):
    """
    CP7: For any detected password field, no correction shall occur.

    Property: When is_password_field() returns True, corrections are never applied
    regardless of input word.
    """
    with patch('custom_autocorrect.main.is_password_field', return_value=True):
        with patch('custom_autocorrect.main.correction_engine.correct') as mock_correct:
            on_word_detected(word)
            mock_correct.assert_not_called()
```

---

### Task 7: Manual Testing

**Test Scenarios**:

1. **Browser Login Forms**:
   - [ ] Open Chrome → navigate to any login page
   - [ ] Type a typo that normally gets corrected (e.g., "teh") in username field → correction SHOULD happen
   - [ ] Type same typo in password field → correction should NOT happen
   - [ ] Check `corrections.log` to verify password field correction was skipped

2. **Windows Credential Dialogs**:
   - [ ] Trigger Windows credential prompt (e.g., `runas /user:Administrator cmd`)
   - [ ] Type in password field → corrections should be skipped

3. **Various Applications**:
   - [ ] Test password field detection in:
     - Edge browser
     - Firefox browser
     - Windows Settings dialogs
     - VS Code (if any password prompts exist)

4. **Fail-Safe Verification**:
   - [ ] Temporarily break password detection (e.g., rename comtypes import)
   - [ ] Verify app continues to work normally (corrections still happen)
   - [ ] App should NOT crash

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/custom_autocorrect/password_detect.py` | Modify | Implement `is_password_field()` |
| `src/custom_autocorrect/__init__.py` | Modify | Export `is_password_field` |
| `src/custom_autocorrect/main.py` | Modify | Add password field check |
| `tests/test_password_detect.py` | Create | Unit and integration tests |
| `tests/test_properties.py` | Modify | Add CP7 property test |

---

## Dependencies

**New Library** (choose one):
- `comtypes` - For direct Windows UI Automation COM access (recommended, smaller)
- `uiautomation` - Higher-level Python wrapper (easier API, larger dependency)

**Add to requirements.txt**:
```
comtypes>=1.1.14  # Windows UI Automation COM bindings
```

**Note**: Both libraries are Windows-only. The code should gracefully handle import failures on non-Windows platforms (for development/testing on Mac).

---

## Acceptance Criteria (from REQ-3)

- [x] THE System SHALL attempt to detect password input fields
- [x] THE System SHALL NOT perform corrections in detected password fields
- [x] THE System SHALL use best-effort detection (may not catch all password fields)

**Correctness Property** (from design.md):

- **CP7: Password Field Safety** - For any detected password field, no correction shall occur.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| UI Automation fails on some apps | Accepted as "best-effort"; fail-safe returns False (corrections continue) |
| Performance impact of COM calls | Check is_password_field() once per word, not per keystroke |
| comtypes not installed | Graceful import failure → corrections continue normally |
| Test reliability on CI | Mock all COM interactions; manual testing covers real detection |

---

## Definition of Done

- [ ] `password_detect.py` implements `is_password_field()` using Windows UI Automation
- [ ] Function returns `False` (fail-safe) on any error
- [ ] `main.py` checks for password field before corrections
- [ ] Debug logging shows when corrections are skipped
- [ ] Unit tests pass with mocked UI Automation
- [ ] Property test validates CP7
- [ ] Manual testing confirms:
  - Corrections skipped in browser password fields
  - Corrections work normally in regular text fields
  - App doesn't crash if detection fails
- [ ] All existing tests still pass
- [ ] `comtypes` added to requirements.txt

---

## Estimated Complexity

- **password_detect.py**: Medium - Windows COM API can be tricky
- **main.py integration**: Low - Single conditional check
- **Testing**: Medium - Mocking COM objects requires careful setup

---

## Notes

1. **Mac Development**: Since password detection uses Windows-only APIs, development on Mac requires mocking. The actual testing must happen on Windows.

2. **Caching Consideration**: For performance, consider caching the password field state briefly (e.g., 100ms). However, given the check only happens on word completion (space pressed), this optimization may be unnecessary.

3. **Alternative Detection Methods**: If UI Automation proves unreliable, fallback strategies include:
   - Check window title for keywords ("Login", "Password", "Sign in")
   - Maintain a blacklist of known password dialog window classes
   - These are less reliable but could supplement UIA detection
