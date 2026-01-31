# Phase 11: Startup & Polish

## Overview

**Goal**: Final polish - auto-start with Windows, handle edge cases, and prepare for v1.0 release.

**Prerequisites**: Phases 1-10 complete. Verified by:
- [x] Keystroke engine captures words correctly
- [x] Rules load from rules.txt and hot-reload on change
- [x] Corrections work via backspace+retype
- [x] Password fields are skipped
- [x] Corrections logged to corrections.log with rotation
- [x] Pattern suggestions tracked from backspace behavior
- [x] System tray icon with menu options
- [x] Win+Shift+A hotkey for adding rules
- [x] PyInstaller packaging creates standalone exe
- [x] README documentation complete

---

## Task 1: Single Instance Enforcement

**Purpose**: Prevent multiple instances of the app from running simultaneously, which would cause keystroke duplication and conflicts.

### Implementation

**File**: `src/custom_autocorrect/single_instance.py` (new)

Create a simple Windows mutex-based single instance check:

```python
# Use win32event for named mutex (already have pywin32 dependency)
# On startup: try to acquire named mutex "CustomAutocorrect_SingleInstance"
# If mutex already exists, show message and exit
# Clean up mutex on shutdown
```

**Approach Options**:
1. **Named Mutex (Recommended)** - System-level, survives crashes
2. **Lock file** - Simple but can leave stale files
3. **Socket binding** - Cross-platform but overkill for Windows-only

### Files to Modify
- `src/custom_autocorrect/single_instance.py` - New module
- `src/custom_autocorrect/main.py` - Import and check at startup
- `src/custom_autocorrect/__init__.py` - Export new classes

### Acceptance Criteria
- [ ] Second instance shows error message and exits
- [ ] Works when running from different directories
- [ ] Works when running as both .py and .exe
- [ ] Mutex released cleanly on normal exit
- [ ] Mutex released on crash (OS handles this)

### Tests
- `tests/test_single_instance.py` - Unit tests for mutex logic

---

## Task 2: Startup Folder Integration

**Purpose**: Allow users to easily enable/disable auto-start with Windows.

### Implementation

**File**: `src/custom_autocorrect/startup.py` (new)

```python
# Functions:
# - get_startup_folder() -> Path  # Returns shell:startup path
# - get_shortcut_path() -> Path   # Returns CustomAutocorrect.lnk path
# - is_startup_enabled() -> bool  # Check if shortcut exists
# - enable_startup() -> bool      # Create shortcut in startup folder
# - disable_startup() -> bool     # Remove shortcut from startup folder
# - get_executable_path() -> Path # Get path to current exe or script
```

**Notes**:
- Use `win32com.client` for creating .lnk shortcuts (pywin32)
- For script mode, shortcut runs: `pythonw.exe -m custom_autocorrect`
- For exe mode, shortcut runs: full path to exe

### Files to Modify
- `src/custom_autocorrect/startup.py` - New module
- `src/custom_autocorrect/tray.py` - Add "Start with Windows" toggle
- `src/custom_autocorrect/__init__.py` - Export new functions

### Tray Menu Addition

Update menu to include checkbox item:

```
View Suggestions (N pending)
Ignore Suggestion...
---
Open Rules File
Open Corrections Log
---
Start with Windows ✓  <- New toggle item
Exit
```

### Acceptance Criteria
- [ ] "Start with Windows" menu item shows current state
- [ ] Clicking toggle adds/removes shortcut from Startup folder
- [ ] Shortcut correctly launches the app on Windows boot
- [ ] Works for both .exe and script modes
- [ ] Menu state updates after toggle

### Tests
- `tests/test_startup.py` - Unit tests for shortcut management (mocked)

---

## Task 3: Graceful Permission Handling

**Purpose**: Handle scenarios where Documents folder isn't writable.

### Current State

The app already has basic error handling in `paths.py`:
- `ensure_app_folder()` raises `OSError` on failure
- `main.py` catches this and exits

### Improvements Needed

1. **Fallback location**: If Documents/CustomAutocorrect fails, try alternative locations
2. **Graceful degradation**: If all storage fails, run with in-memory rules only
3. **User notification**: Show clear message about what went wrong

### Implementation

**File**: `src/custom_autocorrect/paths.py` - Enhance existing functions

```python
# Priority order for app folder:
# 1. Documents/CustomAutocorrect/
# 2. LOCALAPPDATA/CustomAutocorrect/
# 3. %USERPROFILE%/CustomAutocorrect/
# 4. App directory (readonly fallback)

# Add: test_write_permission(path) -> bool
# Add: find_writable_location() -> Optional[Path]
```

**File**: `src/custom_autocorrect/main.py` - Improve startup handling

```python
# On startup:
# 1. Try primary location
# 2. If fails, try fallbacks
# 3. If all fail, show tray notification and continue with limited functionality
# 4. Log which location is being used
```

### Acceptance Criteria
- [ ] App finds writable location automatically
- [ ] Falls back to LOCALAPPDATA if Documents fails
- [ ] Shows notification when using fallback location
- [ ] Still starts even if no writable location (limited mode)

### Tests
- Update `tests/test_paths.py` with fallback location tests

---

## Task 4: Rules File Recovery

**Purpose**: Handle corrupted or missing rules file gracefully.

### Current State

The app already has good handling:
- `RuleParser.parse_file()` skips invalid lines and collects errors
- `RuleMatcher.load()` logs warnings for parse errors
- `main.py` displays parse errors at startup

### Improvements Needed

1. **Auto-backup**: Before reload, backup previous valid rules
2. **Recovery option**: Tray menu option to restore from backup
3. **Validation dialog**: After hotkey add, show if rule was invalid

### Implementation

**File**: `src/custom_autocorrect/rules.py` - Add backup functionality

```python
# Add to RuleFileWatcher:
# - Before reload: save current rules to rules.txt.bak if rules are valid
# - Add method: restore_from_backup() -> bool

# Add validation feedback:
# - After hotkey add, validate the added rule parses correctly
```

**File**: `src/custom_autocorrect/tray.py` - Add recovery menu option

Only show "Restore Rules Backup" if backup file exists.

### Acceptance Criteria
- [ ] rules.txt.bak created when valid rules exist
- [ ] Backup updated each time rules.txt changes
- [ ] Tray menu shows "Restore Rules Backup" when backup exists
- [ ] Restore replaces rules.txt with backup

### Tests
- Add backup/restore tests to `tests/test_rules.py`

---

## Task 5: Enhanced Error Reporting

**Purpose**: Give users clear feedback when something goes wrong.

### Implementation

**File**: `src/custom_autocorrect/main.py` - Improve error messages

Add user-friendly error dialog for critical failures:
- Keyboard hook permission denied
- No writable storage location
- Another instance running

Use `tkinter.messagebox` for critical errors (already available).

### Tray Notifications

For non-critical issues, use Windows toast notifications or tray icon balloon tips:
- "Using fallback storage location"
- "Some rules failed to parse"
- "Win+Shift+A hotkey failed to register"

**Note**: `pystray` supports `.notify()` for balloon tips on Windows.

### Acceptance Criteria
- [ ] Critical errors show dialog with clear message
- [ ] Non-critical warnings show tray notification
- [ ] Error messages explain what user can do

---

## Task 6: Final Testing & Verification

### Manual Testing Checklist

Create `TESTING.md` with comprehensive checklist:

**Core Functionality**
- [ ] Type "teh " → corrected to "the "
- [ ] Type "TEH " → corrected to "THE "
- [ ] Type "Teh " → corrected to "The "
- [ ] Type "Teheran " → NOT corrected (whole word rule)
- [ ] Edit rules.txt → rules reload automatically
- [ ] Press Ctrl+Z after correction → undo works

**Password Protection**
- [ ] Browser login form → corrections skipped
- [ ] Windows credential dialog → corrections skipped

**System Tray**
- [ ] Icon appears in system tray
- [ ] "View Suggestions" shows dialog
- [ ] "Ignore Suggestion" adds to ignore.txt
- [ ] "Open Rules File" opens in editor
- [ ] "Open Corrections Log" opens in editor
- [ ] "Exit" cleanly shuts down app

**Hotkey**
- [ ] Win+Shift+A opens add rule dialog
- [ ] Adding rule works from any application
- [ ] New rule immediately active

**Pattern Detection**
- [ ] Type "hte", backspace, type "the" × 5 → appears in suggestions
- [ ] Ignored patterns don't reappear

**Startup & Lifecycle**
- [ ] First run creates Documents/CustomAutocorrect folder
- [ ] First run creates sample rules.txt
- [ ] Second instance shows error and exits
- [ ] "Start with Windows" toggle works
- [ ] App survives sleep/wake cycle

**Applications to Test**
- [ ] Notepad
- [ ] Chrome (text field)
- [ ] VS Code
- [ ] Microsoft Word
- [ ] Windows Search box

### Acceptance Criteria
- [ ] All checklist items pass
- [ ] No crashes during extended use
- [ ] Memory usage stays reasonable (<50 MB)

---

## Task 7: GitHub Release v1.0.0

### Pre-Release Checklist

1. **Version verification**
   - [ ] `__version__` in `__init__.py` is "1.0.0"
   - [ ] Version in `pyproject.toml` is "1.0.0"

2. **Build verification**
   - [ ] `python build.py` completes successfully
   - [ ] All tests pass
   - [ ] `dist/CustomAutocorrect.exe` created
   - [ ] Exe size is reasonable (~20-30 MB)

3. **Test executable**
   - [ ] Run exe on clean Windows user account
   - [ ] Core functionality works
   - [ ] No missing DLL errors

4. **Documentation**
   - [ ] README.md is complete
   - [ ] Download instructions point to Releases page
   - [ ] Antivirus instructions included

### Release Process

1. Create git tag: `git tag -a v1.0.0 -m "Version 1.0.0 - First release"`
2. Push tag: `git push origin v1.0.0`
3. On GitHub:
   - Go to Releases → Create new release
   - Select tag v1.0.0
   - Title: "Custom Autocorrect v1.0.0"
   - Write release notes (features, known issues)
   - Attach `CustomAutocorrect.exe`
   - Publish release

### Release Notes Template

```markdown
## Custom Autocorrect v1.0.0

First public release!

### Features
- Silent typo correction based on user-defined rules
- Casing preservation (lowercase, Capitalized, UPPERCASE)
- Pattern suggestion from typing behavior
- System tray integration with quick access menu
- Win+Shift+A hotkey for adding new rules
- Password field protection
- Rolling correction log

### Installation
1. Download `CustomAutocorrect.exe` below
2. Run as Administrator for best results
3. Right-click the tray icon to configure

### Known Issues
- Some antivirus software may flag the executable (false positive)
- Password field detection is best-effort

### System Requirements
- Windows 10 or Windows 11
- Administrator privileges recommended
```

---

## Files Summary

### New Files
| File | Purpose |
|------|---------|
| `src/custom_autocorrect/single_instance.py` | Prevent duplicate instances |
| `src/custom_autocorrect/startup.py` | Windows Startup folder integration |
| `tests/test_single_instance.py` | Single instance tests |
| `tests/test_startup.py` | Startup integration tests |
| `TESTING.md` | Manual testing checklist |

### Modified Files
| File | Changes |
|------|---------|
| `src/custom_autocorrect/main.py` | Single instance check, improved error handling |
| `src/custom_autocorrect/paths.py` | Fallback locations, permission checks |
| `src/custom_autocorrect/rules.py` | Backup/restore functionality |
| `src/custom_autocorrect/tray.py` | "Start with Windows" toggle, restore backup option |
| `src/custom_autocorrect/__init__.py` | Export new modules |

---

## Implementation Order

1. **Single Instance** (Task 1) - Critical for preventing conflicts
2. **Startup Integration** (Task 2) - High value user feature
3. **Permission Handling** (Task 3) - Improves reliability
4. **Rules Recovery** (Task 4) - Improves reliability
5. **Error Reporting** (Task 5) - Improves user experience
6. **Testing** (Task 6) - Verify everything works
7. **Release** (Task 7) - Ship it!

---

## Requirements Satisfied

This phase completes the following requirements:

| Requirement | Criterion | How Satisfied |
|-------------|-----------|---------------|
| REQ-8 | Support running from Windows Startup folder | Task 2: Startup folder shortcut |
| REQ-8 | Run as background process with minimal resources | Already implemented; Task 6 verifies |
| REQ-8 | Create folder/files if missing | Already implemented; Task 3 enhances |
| REQ-9 | Store all files in Documents/CustomAutocorrect | Already implemented; Task 3 adds fallbacks |

**Success Criteria from implementation_plan.md**:
- [ ] Single .exe runs without Python installed (Phase 10 - done)
- [ ] App available for download via GitHub Releases (Task 7)
- [ ] App can auto-start with Windows (Task 2)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Mutex fails on some Windows versions | Fall back to lock file if win32event unavailable |
| Startup shortcut creation requires admin | Use current user Startup folder (no admin needed) |
| Antivirus blocks exe | Already documented; consider code signing for v1.1 |
| Rules backup fills disk | Only keep one backup file, overwrite on each reload |

---

## Estimated Effort

| Task | Complexity | Files |
|------|------------|-------|
| Task 1: Single Instance | Low | 3 |
| Task 2: Startup Integration | Medium | 4 |
| Task 3: Permission Handling | Low | 2 |
| Task 4: Rules Recovery | Low | 2 |
| Task 5: Error Reporting | Low | 1 |
| Task 6: Testing | Manual | 1 |
| Task 7: Release | Process | 0 |

Most tasks are straightforward with clear implementation paths. The codebase is well-structured from previous phases, making additions clean.
