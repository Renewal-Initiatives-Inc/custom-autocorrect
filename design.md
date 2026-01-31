# Design: Custom Autocorrect

## 1. Overview

### Problem
When typing quickly, users make the same 10-20 typos repeatedly. Current solutions either only highlight errors (requiring manual fixes) or attempt auto-learning that corrupts common words (as seen in EkaKey's critical bugs). The user needs silent, reliable correction of known typo patterns without interrupting their cognitive flow.

### Solution Approach
A lightweight Windows background application ("Smart Tracker") that:
1. Watches keystrokes system-wide
2. Maintains a simple lookup table of typo→correction rules
3. Silently corrects matches via backspace+retype when space is pressed
4. Passively logs potential typos (non-dictionary words typed 5+ times) for user review
5. Never auto-creates rules—user confirms everything

This approach prioritizes reliability and user control over intelligence and automation.

---

## 2. Key Design Principles

These principles are derived from requirements and lessons learned from EkaKey's failures:

### P1: User Confirms All Rules
Never auto-create correction rules. The app may suggest patterns, but the user must explicitly add them to rules.txt. This prevents the "I→yiam" corruption bug that plagued EkaKey.

### P2: Simple Rule Engine
The correction engine is a pure lookup table: `typo → correction`. No phonetic matching, no fuzzy logic, no ML inference. Simplicity ensures predictability.

### P3: Minimal State
Track only the current word buffer. Don't maintain edit history, word chains, or complex state machines. Reset state on every delimiter. This avoids the edge cases that caused EkaKey's cross-word-boundary bugs.

### P4: Fail Safe
When uncertain, do nothing. A missed correction is far better than a wrong one. If the app can't determine context (e.g., unclear if password field), skip the correction.

### P5: Respect Cognitive Flow
Typing is thinking. The tool must be invisible during operation—no popups, no sounds, no confirmations. Feedback happens asynchronously via log files the user can check later.

---

## 3. Technology Approach

> **Note**: This section will be populated after running `/tech-stack` to make technology decisions.

Preliminary considerations:
- **Language**: Python (rapid development, good keyboard hooking libraries)
- **Keyboard Hooks**: `keyboard` library or `pynput` (to be evaluated)
- **System Tray**: `pystray` for cross-platform tray icon
- **Packaging**: PyInstaller for single-executable distribution
- **Dictionary**: Bundled word list file

---

## 4. Correctness Properties

These universal rules must hold across all valid inputs:

### CP1: Rule Integrity
**For any** correction that occurs, **the trigger must exactly match** a key in rules.txt (case-insensitive matching, case-preserved output).

*Validates*: REQ-1 (criteria 3, 5, 6)

### CP2: Whole-Word Guarantee
**For any** typed text containing a trigger as a substring of a larger word, **no correction shall occur**.

*Validates*: REQ-1 (criterion 5)

### CP3: Casing Preservation
**For any** correction where trigger has casing pattern P, **the correction shall have the same casing pattern P**.

*Validates*: REQ-1 (criterion 6)

### CP4: Suggestion Threshold
**For any** word appearing in suggestions.txt, **that word must have been typed at least 5 times** and not be in the dictionary, custom-words.txt, or ignore.txt.

*Validates*: REQ-4 (criteria 3, 5), REQ-5 (criterion 4)

### CP5: Log Rotation
**For any** state of corrections.log, **the file shall contain at most 100 entries**.

*Validates*: REQ-6 (criteria 3, 4)

### CP6: No Auto-Learning
**For any** system state, **rules.txt shall only contain entries explicitly added by the user** (via hotkey or manual editing).

*Validates*: REQ-2, Out of Scope (auto-learning)

### CP7: Password Field Safety
**For any** detected password field, **no correction shall occur**.

*Validates*: REQ-3 (criteria 1, 2)

---

## 5. Business Logic Flows

### Flow 1: Keystroke Processing

```
User types character
    │
    ├─► Is password field detected?
    │       Yes → Append to buffer, no processing, DONE
    │
    ├─► Is character a space (delimiter)?
    │       No → Append to buffer, DONE
    │       Yes ↓
    │
    ├─► Extract word from buffer
    │
    ├─► Is word in rules.txt (case-insensitive)?
    │       No → Log word for suggestion tracking, clear buffer, DONE
    │       Yes ↓
    │
    ├─► Get correction from rules
    ├─► Apply casing from original word
    ├─► Perform correction (backspace × word length, type correction, type space)
    ├─► Log to corrections.log
    └─► Clear buffer, DONE
```

### Flow 2: Add Rule via Hotkey (Win+Shift+A)

```
User presses Win+Shift+A
    │
    ├─► Prompt for typo word (simple input dialog or clipboard-based)
    ├─► Prompt for correction word
    ├─► Validate: typo ≠ correction, both non-empty
    │       Invalid → Show error, abort
    │
    ├─► Append "typo=correction" to rules.txt
    ├─► Reload rules into memory
    └─► DONE
```

### Flow 3: Suggestion Tracking

```
Word typed (not in rules.txt)
    │
    ├─► Is word in dictionary OR custom-words.txt?
    │       Yes → DONE (valid word, no tracking)
    │
    ├─► Is word in ignore.txt?
    │       Yes → DONE (user said ignore)
    │
    ├─► Increment count for word in memory
    ├─► Has count reached 5?
    │       No → DONE
    │       Yes ↓
    │
    ├─► Is word already in suggestions.txt?
    │       Yes → Update count in file
    │       No → Append word with count to suggestions.txt
    └─► DONE
```

### Flow 4: Ignore Suggestion (via Tray Menu)

```
User clicks "Ignore Suggestion" in tray menu
    │
    ├─► Display list of current suggestions
    ├─► User selects word to ignore
    ├─► Append word to ignore.txt
    ├─► Remove word from suggestions.txt
    ├─► Remove word from in-memory tracking
    └─► DONE
```

### Flow 5: Correction Logging

```
Correction performed
    │
    ├─► Get current timestamp
    ├─► Get active window title
    ├─► Format log entry: "timestamp | original → corrected | window"
    │
    ├─► Read corrections.log
    ├─► If entry count ≥ 100, remove oldest entry
    ├─► Append new entry
    └─► Write corrections.log, DONE
```

---

## 6. Error Handling Strategy

### User Errors

| Error | Handling |
|-------|----------|
| Invalid rule format in rules.txt | Skip line, log warning to console/debug log |
| Empty typo or correction in hotkey | Show brief error message, don't save |
| Typo equals correction | Show brief error message, don't save |

### System Errors

| Error | Handling |
|-------|----------|
| Cannot access Documents folder | Fall back to app directory, warn on startup |
| Cannot create/write files | Show tray notification, continue running (corrections still work in memory) |
| Keyboard hook fails to install | Exit with error message—app cannot function |
| Active window detection fails | Log correction with "Unknown" as window title |
| Dictionary file missing | Bundle dictionary in executable; if missing, disable suggestion feature |

### Recovery Strategy

- **Files corrupted**: Delete and recreate with empty defaults on next startup
- **App crashes**: Startup folder ensures restart on next login
- **Rules file locked**: Retry with backoff; skip reload if persistent

---

## 7. Testing Strategy

### Unit Tests

| Component | Test Cases |
|-----------|------------|
| Rule Parser | Valid rules, comments, blank lines, invalid format, unicode |
| Casing Logic | lowercase→lowercase, Capitalized→Capitalized, UPPER→UPPER, mIxEd→mIxEd |
| Whole-Word Matching | Exact match, substring (should NOT match), start of word, end of word |
| Log Rotation | Under limit, at limit, over limit, empty log |
| Suggestion Threshold | Count < 5, count = 5, count > 5, already suggested |

### Property-Based Tests

| Property | Generator |
|----------|-----------|
| CP1: Rule Integrity | Generate random rules, random triggers, verify only exact matches correct |
| CP2: Whole-Word Guarantee | Generate words containing triggers as substrings, verify no correction |
| CP3: Casing Preservation | Generate triggers with various casings, verify correction matches |
| CP5: Log Rotation | Generate sequences of 200+ corrections, verify log never exceeds 100 |

### Integration Tests

| Scenario | Verification |
|----------|--------------|
| Full correction flow | Type trigger + space, verify correction applied |
| Hotkey rule addition | Press hotkey, add rule, verify rule works immediately |
| Suggestion lifecycle | Type non-dictionary word 5x, verify appears in suggestions |
| Ignore workflow | Ignore suggestion via tray, verify never suggested again |
| Startup | Launch app, verify tray icon appears, rules loaded |

### Manual Testing Checklist

- [ ] Corrections work in Notepad
- [ ] Corrections work in Chrome (text fields)
- [ ] Corrections work in VS Code
- [ ] Corrections work in Microsoft Word
- [ ] Password fields are skipped (test in browser login)
- [ ] Ctrl+Z undoes correction
- [ ] Tray menu functions all work
- [ ] App survives sleep/wake cycle
- [ ] App starts on Windows login

---

## 8. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Typing                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Keyboard Hook (OS-level)                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Word Buffer                                 │
│                   (current word being typed)                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐       ┌──────────────────┐
            │ Rules Lookup │       │ Suggestion Track │
            │ (rules.txt)  │       │ (dictionary +    │
            └──────────────┘       │  suggestions.txt)│
                    │              └──────────────────┘
                    ▼                       │
            ┌──────────────┐               │
            │ Correction   │               │
            │ Engine       │               │
            │ (backspace + │               │
            │  retype)     │               │
            └──────────────┘               │
                    │                       │
                    ▼                       ▼
            ┌──────────────┐       ┌──────────────────┐
            │ corrections  │       │ suggestions.txt  │
            │ .log         │       │ ignore.txt       │
            └──────────────┘       └──────────────────┘

                    ┌─────────────────────┐
                    │    System Tray      │
                    │  (view, ignore,     │
                    │   open files, exit) │
                    └─────────────────────┘
```

---

## 9. File System Layout

```
Documents/
└── CustomAutocorrect/
    ├── rules.txt           # User-defined corrections
    ├── suggestions.txt     # Detected potential typos
    ├── ignore.txt          # Words to never suggest
    ├── corrections.log     # Rolling log (max 100 entries)
    └── custom-words.txt    # User dictionary additions

[App Location]/
└── CustomAutocorrect.exe   # Single executable (contains bundled dictionary)
```
