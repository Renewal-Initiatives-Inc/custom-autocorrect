# Phase 4: Correction Engine - Execution Plan

## Overview

**Goal**: Actually perform corrections by simulating backspace and retyping with casing preservation.

**Deliverable**: App that silently corrects typos as you type in any application.

**Current State**: Phase 3 complete. The app detects matches and logs "Would correct X → Y". Now we need to actually perform the corrections.

---

## Dependencies Verification

Before starting Phase 4, verify Phase 3 is complete:

- [ ] All 125 tests pass (`pytest tests/`)
- [ ] `RuleMatcher.match(word)` returns Rule objects with typo and correction
- [ ] `main.py` callback receives completed words and matches them against rules
- [ ] Rules are loaded from `Documents/CustomAutocorrect/rules.txt`

---

## Task Breakdown

### Task 1: Implement Casing Detection and Application

**File**: `src/custom_autocorrect/correction.py`

**Functions to implement**:

```python
def detect_casing_pattern(word: str) -> str:
    """Detect the casing pattern of a word.

    Returns:
        "lowercase" - all lowercase (e.g., "teh")
        "capitalized" - first letter uppercase, rest lowercase (e.g., "Teh")
        "uppercase" - all uppercase (e.g., "TEH")
        "mixed" - any other pattern (e.g., "tEh", "TeTe")
    """

def apply_casing(original_word: str, correction: str) -> str:
    """Apply the casing pattern from original_word to correction.

    Examples:
        apply_casing("teh", "the") -> "the"
        apply_casing("Teh", "the") -> "The"
        apply_casing("TEH", "the") -> "THE"
        apply_casing("tEh", "the") -> "the"  # mixed falls back to correction as-is
    """
```

**Acceptance Criteria** (from REQ-1, criterion 6):
- lowercase → lowercase
- Capitalized → Capitalized
- UPPERCASE → UPPERCASE
- Mixed case → Use correction as-is (safe fallback)

**Correctness Property CP3**: For any correction where trigger has casing pattern P, the correction shall have the same casing pattern P.

---

### Task 2: Implement Keyboard Simulation

**File**: `src/custom_autocorrect/correction.py`

**Functions to implement**:

```python
def perform_correction(typo_length: int, correction: str) -> bool:
    """Perform correction via keyboard simulation.

    Algorithm:
    1. Send backspace key `typo_length + 1` times (erase typed word + the space that triggered it)
    2. Type the correction text
    3. Type a space (restore the delimiter)

    Args:
        typo_length: Number of characters in the original typo
        correction: The corrected text to type

    Returns:
        True if correction was performed, False on error

    Note: The +1 accounts for the space that was just typed to trigger the correction.
    We need to erase it too, then retype after the correction.
    """
```

**Implementation details**:
- Use `keyboard.press_and_release('backspace')` for erasing
- Use `keyboard.write(text)` for typing the correction
- Consider adding small delays (e.g., 10ms) between operations for reliability in slower applications
- Wrap in try/except for error handling (fail safe - P4 design principle)

**Timing considerations**:
- Some applications may need delays between keystrokes
- Start without delays, add if testing reveals issues
- Make delay configurable (constant at module level)

---

### Task 3: Create CorrectionEngine Class

**File**: `src/custom_autocorrect/correction.py`

**Class to implement**:

```python
class CorrectionEngine:
    """Performs typo corrections with casing preservation.

    Encapsulates the correction logic to separate concerns from keystroke detection.
    """

    def __init__(self, delay_ms: int = 0):
        """Initialize the correction engine.

        Args:
            delay_ms: Delay in milliseconds between keyboard operations (default 0)
        """

    def correct(self, original_word: str, rule_correction: str) -> bool:
        """Apply a correction with proper casing.

        Args:
            original_word: The typo as typed (with original casing)
            rule_correction: The correction from the rule (stored casing)

        Returns:
            True if correction was performed successfully
        """
```

**Benefits of class-based design**:
- Configurable delay for testing/tuning
- Can track correction statistics later (Phase 5)
- Clear separation of concerns
- Easy to mock in tests

---

### Task 4: Integrate with Main Application

**File**: `src/custom_autocorrect/main.py`

**Modify `on_word_detected` callback**:

```python
# Before (Phase 3):
def on_word_detected(word: str) -> None:
    rule = _matcher.match(word)
    if rule:
        logger.info(f"Would correct: '{word}' -> '{rule.correction}'")
        print(f"Would correct: '{word}' -> '{rule.correction}'")

# After (Phase 4):
def on_word_detected(word: str) -> None:
    rule = _matcher.match(word)
    if rule:
        corrected = _correction_engine.correct(word, rule.correction)
        if corrected:
            logger.info(f"Corrected: '{word}' -> '{rule.correction}'")
```

**Changes needed**:
1. Import `CorrectionEngine` from `correction` module
2. Create `_correction_engine` global instance
3. Update callback to call `correct()` instead of just logging

---

### Task 5: Write Unit Tests for Casing Logic

**File**: `tests/test_correction.py`

**Test cases**:

```python
class TestDetectCasingPattern:
    def test_lowercase(self):
        assert detect_casing_pattern("teh") == "lowercase"
        assert detect_casing_pattern("hello") == "lowercase"

    def test_capitalized(self):
        assert detect_casing_pattern("Teh") == "capitalized"
        assert detect_casing_pattern("Hello") == "capitalized"

    def test_uppercase(self):
        assert detect_casing_pattern("TEH") == "uppercase"
        assert detect_casing_pattern("HELLO") == "uppercase"

    def test_mixed(self):
        assert detect_casing_pattern("tEh") == "mixed"
        assert detect_casing_pattern("hElLo") == "mixed"
        assert detect_casing_pattern("HeLLo") == "mixed"

    def test_single_character(self):
        assert detect_casing_pattern("a") == "lowercase"
        assert detect_casing_pattern("A") == "uppercase"

    def test_empty_string(self):
        # Edge case: should handle gracefully
        assert detect_casing_pattern("") == "lowercase"


class TestApplyCasing:
    def test_lowercase_to_lowercase(self):
        assert apply_casing("teh", "the") == "the"
        assert apply_casing("adn", "and") == "and"

    def test_capitalized_to_capitalized(self):
        assert apply_casing("Teh", "the") == "The"
        assert apply_casing("Adn", "and") == "And"

    def test_uppercase_to_uppercase(self):
        assert apply_casing("TEH", "the") == "THE"
        assert apply_casing("ADN", "and") == "AND"

    def test_mixed_falls_back_to_correction(self):
        # Mixed case uses correction as-is (safe fallback)
        assert apply_casing("tEh", "the") == "the"
        assert apply_casing("hElLo", "hello") == "hello"

    def test_different_lengths(self):
        # Correction may be different length than original
        assert apply_casing("THT", "that") == "THAT"
        assert apply_casing("Tht", "that") == "That"

    def test_preserves_unicode(self):
        # Should handle unicode characters
        assert apply_casing("cafe", "cafe") == "cafe"
        assert apply_casing("CAFE", "cafe") == "CAFE"
```

---

### Task 6: Write Unit Tests for Keyboard Simulation

**File**: `tests/test_correction.py`

**Test cases with mocked keyboard**:

```python
from unittest.mock import patch, MagicMock

class TestPerformCorrection:
    @patch('custom_autocorrect.correction.keyboard')
    def test_backspace_count(self, mock_keyboard):
        """Should send correct number of backspaces."""
        perform_correction(3, "the")

        # 3 (typo) + 1 (space) = 4 backspaces
        backspace_calls = [
            call for call in mock_keyboard.press_and_release.call_args_list
            if call[0][0] == 'backspace'
        ]
        assert len(backspace_calls) == 4

    @patch('custom_autocorrect.correction.keyboard')
    def test_types_correction(self, mock_keyboard):
        """Should type the correction text."""
        perform_correction(3, "the")

        mock_keyboard.write.assert_called_once()
        # Should include correction + space
        assert "the" in str(mock_keyboard.write.call_args)

    @patch('custom_autocorrect.correction.keyboard')
    def test_types_space_after(self, mock_keyboard):
        """Should type space after correction."""
        perform_correction(3, "the")

        # Either write("the ") or write("the") + press_and_release("space")
        call_str = str(mock_keyboard.write.call_args)
        assert "the " in call_str or mock_keyboard.press_and_release.called


class TestCorrectionEngine:
    @patch('custom_autocorrect.correction.keyboard')
    def test_applies_casing_before_correction(self, mock_keyboard):
        engine = CorrectionEngine()
        engine.correct("TEH", "the")

        # Should write "THE " (uppercase)
        mock_keyboard.write.assert_called_once()
        assert "THE" in str(mock_keyboard.write.call_args)

    @patch('custom_autocorrect.correction.keyboard')
    def test_returns_true_on_success(self, mock_keyboard):
        engine = CorrectionEngine()
        result = engine.correct("teh", "the")
        assert result is True

    @patch('custom_autocorrect.correction.keyboard')
    def test_returns_false_on_error(self, mock_keyboard):
        mock_keyboard.press_and_release.side_effect = Exception("Keyboard error")
        engine = CorrectionEngine()
        result = engine.correct("teh", "the")
        assert result is False
```

---

### Task 7: Write Property-Based Tests for Casing Preservation (CP3)

**File**: `tests/test_properties.py`

**Add to existing property tests**:

```python
from hypothesis import given, strategies as st
from custom_autocorrect.correction import apply_casing, detect_casing_pattern

class TestCasingPreservationProperties:
    @given(st.text(alphabet=st.characters(whitelist_categories=('L',)), min_size=1, max_size=20))
    def test_lowercase_pattern_preserved(self, word):
        """CP3: lowercase input produces lowercase output."""
        original = word.lower()
        correction = "test"  # Any lowercase correction
        result = apply_casing(original, correction)
        assert result == result.lower()

    @given(st.text(alphabet=st.characters(whitelist_categories=('L',)), min_size=1, max_size=20))
    def test_uppercase_pattern_preserved(self, word):
        """CP3: uppercase input produces uppercase output."""
        original = word.upper()
        correction = "test"
        result = apply_casing(original, correction)
        assert result == result.upper()

    @given(st.text(alphabet=st.characters(whitelist_categories=('L',)), min_size=1, max_size=20))
    def test_capitalized_pattern_preserved(self, word):
        """CP3: capitalized input produces capitalized output."""
        original = word.capitalize()
        correction = "test"
        result = apply_casing(original, correction)
        assert result == result.capitalize()

    @given(
        st.text(alphabet=st.characters(whitelist_categories=('L',)), min_size=1, max_size=20),
        st.text(alphabet=st.characters(whitelist_categories=('L',)), min_size=1, max_size=20)
    )
    def test_casing_never_crashes(self, original, correction):
        """apply_casing should never raise for any string inputs."""
        # Should not raise
        result = apply_casing(original, correction)
        assert isinstance(result, str)
```

---

### Task 8: Manual Testing in Applications

**Test in these applications** (per implementation_plan.md):

1. **Notepad**
   - [ ] Create rules.txt with `teh=the`
   - [ ] Open Notepad, type "teh " (with space)
   - [ ] Verify "teh" is replaced with "the"
   - [ ] Verify Ctrl+Z undoes the correction

2. **Chrome text field**
   - [ ] Open Chrome, go to any site with a text input
   - [ ] Type "teh " in the input
   - [ ] Verify correction occurs
   - [ ] Verify Ctrl+Z undoes

3. **VS Code** (if available on Windows machine)
   - [ ] Open a file, type "teh "
   - [ ] Verify correction occurs

4. **Test casing preservation**:
   - [ ] Type "teh " → should become "the"
   - [ ] Type "Teh " → should become "The"
   - [ ] Type "TEH " → should become "THE"

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `src/custom_autocorrect/correction.py` | **Modify** | Replace stub with full implementation |
| `src/custom_autocorrect/__init__.py` | **Modify** | Export `CorrectionEngine`, `apply_casing` |
| `src/custom_autocorrect/main.py` | **Modify** | Integrate CorrectionEngine into callback |
| `tests/test_correction.py` | **Modify** | Replace skipped placeholder with full tests |
| `tests/test_properties.py` | **Modify** | Add CP3 property-based tests |

---

## Acceptance Criteria Satisfied

From **REQ-1: Silent Typo Correction**:

| Criterion | Status |
|-----------|--------|
| 1. Monitor keystrokes system-wide | ✓ (Phase 2) |
| 2. Load correction rules from rules.txt | ✓ (Phase 3) |
| 3. Detect when typed word matches rule | ✓ (Phase 3) |
| **4. Replace trigger with correction via backspace+retype** | **Phase 4** |
| 5. Only match whole words | ✓ (Phase 2-3) |
| **6. Preserve original casing pattern** | **Phase 4** |
| 7. No visual/audio feedback | ✓ (by design) |
| 8. Support Ctrl+Z to undo | ✓ (native app behavior) |

**Correctness Properties**:
- CP1: Rule Integrity ✓ (Phase 3)
- CP2: Whole-Word Guarantee ✓ (Phase 2)
- **CP3: Casing Preservation - Phase 4**

---

## Implementation Order

1. **Task 1**: Implement casing detection and application functions
2. **Task 5**: Write unit tests for casing logic (test-first approach)
3. **Task 2**: Implement keyboard simulation function
4. **Task 3**: Create CorrectionEngine class
5. **Task 6**: Write unit tests for keyboard simulation
6. **Task 4**: Integrate with main.py
7. **Task 7**: Add property-based tests for CP3
8. **Task 8**: Manual testing in Notepad and Chrome

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Keyboard simulation timing issues | Add configurable delay parameter; start at 0ms, increase if needed |
| Corrections appear garbled in some apps | Test in multiple apps; document any incompatible apps |
| Backspace count off-by-one | Verify: typo_length + 1 (for the space) |
| Unicode characters break casing | Test with unicode; use Python's built-in str methods |
| keyboard library requires admin | Document requirement; test in non-admin mode to confirm behavior |

---

## Definition of Done

- [ ] All casing patterns work: lowercase, Capitalized, UPPERCASE
- [ ] Corrections appear silently (no visible delay or flicker)
- [ ] All new tests pass (unit + property-based)
- [ ] Test coverage for correction.py ≥ 90%
- [ ] Manual testing passes in Notepad and Chrome
- [ ] Ctrl+Z undoes corrections via native app undo
- [ ] No regressions in existing tests (125 still passing)
- [ ] Code committed with descriptive message
