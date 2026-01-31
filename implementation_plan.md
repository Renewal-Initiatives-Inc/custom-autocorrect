# Implementation Plan: Custom Autocorrect

## Overview

Build a lightweight Windows background application that silently corrects known typos based on user-defined rules. The app monitors keystrokes system-wide, performs corrections via backspace+retype, and passively tracks potential typos for user review.

**Tech Stack**: Python + keyboard hooks + pystray + PyInstaller
**Development**: Windows machine (remote access from Mac)
**Distribution**: GitHub Releases (.exe download)

---

## Phase 0: Technology Stack Decisions ✓

See [technology_decisions.md](technology_decisions.md) for complete decisions on:
- Language & Libraries (Python)
- Development Environment (Windows with remote access)
- Testing Framework (pytest + Hypothesis)
- Version Control & Distribution (GitHub)

---

## Phase 1: Development Environment Setup ✓

**Goal**: Get the Windows development environment ready with remote access, Python, git, and GitHub.

**Tasks**:
1. Set up remote access from Mac to Windows PC
   - Option A: Enable Windows Remote Desktop, connect via Mac's Microsoft Remote Desktop app
   - Option B: Install OpenSSH Server on Windows, use VS Code Remote-SSH extension
2. Install Python 3.11+ on Windows
3. Install git on Windows and configure user identity
4. Create GitHub repository for the project
5. Clone repository to Windows development machine
6. Create virtual environment and install initial dependencies
7. Create basic project structure with placeholder files
8. Verify round-trip: edit code → commit → push → see on GitHub

**Deliverable**: Working development environment where you can write Python code on Windows (accessed from Mac), run it, and push to GitHub.

---

## Phase 2: Core Keystroke Engine ✓

**Goal**: Build the foundation - capture keystrokes, maintain a word buffer, detect word boundaries.

**Tasks**:
1. Evaluate `keyboard` vs `pynput` library for keystroke capture
2. Implement global keyboard hook that captures all keystrokes
3. Implement word buffer that accumulates characters
4. Detect space as word delimiter and extract completed words
5. Handle backspace (remove last character from buffer)
6. Handle special keys that should clear the buffer (Enter, Tab, Escape, arrow keys)
7. Write unit tests for buffer logic

**Deliverable**: Running app that prints each completed word to console when space is pressed.

---

## Phase 3: Rule Loading & Matching ✓

**Goal**: Load correction rules from file and match typed words against them.

**Tasks**:
1. Create `Documents/CustomAutocorrect/` folder structure
2. Implement rules.txt parser (handle `typo=correction` format, comments, blank lines)
3. Implement file watcher to reload rules when file changes
4. Implement case-insensitive rule lookup
5. Implement whole-word matching (ensure "teh" in "Teheran" doesn't match)
6. Write unit tests for rule parsing and matching
7. Write property-based tests for rule integrity (CP1)

**Deliverable**: App that detects when a typed word matches a rule and logs "Would correct X → Y".

---

## Phase 4: Correction Engine ✓

**Goal**: Actually perform corrections by simulating backspace and retyping.

**Tasks**:
1. Implement correction via keyboard simulation (backspace × word length, type correction, type space)
2. Implement casing preservation logic:
   - lowercase → lowercase
   - Capitalized → Capitalized
   - UPPERCASE → UPPERCASE
3. Test correction in Notepad
4. Test correction in Chrome text field
5. Write unit tests for casing logic
6. Write property-based tests for casing preservation (CP3)

**Deliverable**: App that silently corrects typos as you type in any application.

---

## Phase 5: Correction Logging ✓

**Goal**: Log corrections to a rolling log file for verification.

**Tasks**:
1. Implement active window title detection (for log context)
2. Implement corrections.log writer with format: `timestamp | original → corrected | window`
3. Implement log rotation (keep max 100 entries)
4. Handle edge cases (unknown window, file locked)
5. Write unit tests for log rotation
6. Write property-based tests for log size limit (CP5)

**Deliverable**: Each correction is logged to `Documents/CustomAutocorrect/corrections.log`.

---

## Phase 6: Password Field Protection ✓

**Goal**: Skip corrections in password fields to avoid breaking passwords.

**Tasks**:
1. Research Windows UI Automation API for detecting password fields
2. Implement password field detection (best-effort)
3. Skip correction when password field is detected
4. Test in browser login forms
5. Test in Windows credential dialogs

**Deliverable**: App skips corrections in detected password fields.

---

## Phase 7: Pattern Suggestion System ✓

**Goal**: Track potential typos (non-dictionary words typed 5+ times) and log suggestions.

**Tasks**:
1. Bundle English word list with the app
2. Implement word frequency counter (in-memory)
3. Implement dictionary lookup
4. Implement custom-words.txt support
5. Implement suggestions.txt writer (words typed 5+ times not in dictionary)
6. Implement ignore.txt support (words to never suggest)
7. Write unit tests for suggestion threshold logic
8. Write property-based tests for suggestion threshold (CP4)

**Deliverable**: Non-dictionary words typed frequently appear in suggestions.txt.

---

## Phase 8: System Tray Integration ✓

**Goal**: Add system tray icon with menu for accessing features.

**Tasks**:
1. Implement tray icon using pystray
2. Implement right-click menu with options:
   - View Suggestions
   - Ignore Suggestion (submenu or dialog)
   - Open Rules File
   - Open Corrections Log
   - Exit
3. Implement "View Suggestions" dialog/window
4. Implement "Ignore Suggestion" functionality
5. Test tray icon persists across sleep/wake

**Deliverable**: App runs with tray icon; all menu options functional.

---

## Phase 9: Add Rule Hotkey ✓

**Goal**: Implement Win+Shift+A hotkey for quickly adding new rules.

**Tasks**:
1. Register global hotkey (Win+Shift+A)
2. Implement simple input dialog for typo and correction
3. Validate input (non-empty, typo ≠ correction)
4. Append new rule to rules.txt
5. Trigger rule reload after addition
6. Test hotkey works system-wide

**Deliverable**: Press Win+Shift+A anywhere to add a new correction rule.

---

## Phase 10: Packaging & Distribution ✓

**Goal**: Package as single .exe and set up GitHub Releases for distribution.

**Tasks**:
1. Create PyInstaller spec file
2. Bundle dictionary file with executable
3. Build .exe and test on clean Windows machine (or different user account)
4. Handle antivirus false positives if they occur (signing optional)
5. Create build script for reproducible builds
6. Create first GitHub Release with .exe attached
7. Document download/installation instructions in README

**Deliverable**: Downloadable .exe on GitHub Releases that runs without Python installed.

**Files Created**:
- `CustomAutocorrect.spec` - PyInstaller configuration
- `build.py` - Reproducible build script
- Updated `resources/create_icon.py` - Now generates both PNG and ICO
- Updated `src/custom_autocorrect/paths.py` - Added bundled resource helpers
- Updated `README.md` - Full installation and usage documentation

---

## Phase 11: Startup & Polish ✓

**Goal**: Final polish - auto-start with Windows, handle edge cases, documentation.

**Tasks**:
1. Implement Startup folder integration (optional auto-start)
2. Test clean first-run experience (creates folders/files if missing)
3. Handle edge cases:
   - Rules file missing or corrupted
   - No write permission to Documents folder
   - App already running (prevent duplicates)
4. Write README with usage instructions
5. Final round of manual testing across apps (Notepad, Chrome, VS Code, Word)
6. Create GitHub Release v1.0

**Deliverable**: Production-ready app with documentation.

**Files Created**:
- `src/custom_autocorrect/single_instance.py` - Prevents duplicate app instances
- `src/custom_autocorrect/startup.py` - Windows Startup folder integration
- `tests/test_single_instance.py` - Single instance tests
- `tests/test_startup.py` - Startup integration tests
- `TESTING.md` - Manual testing checklist

**Files Modified**:
- `src/custom_autocorrect/main.py` - Added single instance check, improved error dialogs
- `src/custom_autocorrect/paths.py` - Added fallback storage locations
- `src/custom_autocorrect/rules.py` - Added backup/restore functionality
- `src/custom_autocorrect/tray.py` - Added "Start with Windows" toggle, restore backup option
- `src/custom_autocorrect/__init__.py` - Exported new modules

---

## Phase Dependencies

```
Phase 1 (Environment Setup)
    ↓
Phase 2 (Keystroke Engine)
    ↓
Phase 3 (Rule Loading) ──────────────────┐
    ↓                                    ↓
Phase 4 (Correction Engine)         Phase 7 (Suggestions)
    ↓                                    ↓
Phase 5 (Logging)                   Phase 8 (System Tray) ←─┐
    ↓                                    ↓                  │
Phase 6 (Password Protection)       Phase 9 (Hotkey) ───────┘
    ↓
    └──────────────┬─────────────────────┘
                   ↓
            Phase 10 (Packaging)
                   ↓
            Phase 11 (Polish)
```

**Parallel work possible**: After Phase 3, work on Phase 7 (Suggestions) can proceed in parallel with Phases 4-6.

---

## Risk Areas & Mitigation

| Risk | Mitigation |
|------|------------|
| Keyboard hook requires admin rights | Document admin requirement; test with limited permissions to confirm behavior |
| Antivirus flags PyInstaller .exe | Expected behavior; document how to add exception; consider code signing later |
| Password field detection unreliable | Accepted in requirements as "best effort"; fail safe (skip correction when uncertain) |
| Correction timing issues in some apps | Test across multiple apps; add small delays if needed |
| Remote development friction | Set up VS Code Remote-SSH for seamless editing experience |

---

## Success Criteria

All functionality implemented. Run TESTING.md checklist on Windows to verify:

- [x] Corrections work silently in Notepad, Chrome, VS Code, and Word
- [x] Only user-defined rules trigger corrections (no auto-learning)
- [x] Password fields are skipped (best-effort)
- [x] Casing is preserved (lowercase, Capitalized, UPPERCASE)
- [x] Ctrl+Z undoes corrections via native app undo
- [x] Tray icon present with functional menu
- [x] Win+Shift+A adds new rules
- [x] Suggestions.txt captures frequent non-dictionary words
- [x] Single .exe runs without Python installed
- [x] App available for download via GitHub Releases
- [x] App can auto-start with Windows (optional)
