# Technology Decisions: Custom Autocorrect

## Purpose
This document records technology choices made during project planning. Each decision includes rationale and tradeoffs to help future maintainers understand "why" not just "what."

## Decision-Making Philosophy
- **Simplicity over sophistication**: Choose boring, proven technology
- **Single-user focus**: No need to over-engineer for scale
- **Windows-first**: Optimize for the target platform
- **Maintainability**: Easy to understand and modify later

## Project Constraints
- **Platform**: Windows only (single user, admin access)
- **Distribution**: Single executable file
- **Storage**: Local plain text files (no database)
- **Network**: Offline only (no cloud sync)
- **User**: Solo maintainer, comfortable editing text files

---

## Decision Log

### Decision 1: Language & Libraries
**Choice**: Python with keyboard hooks + system tray libraries

**Date**: 2026-01-31

**Options Considered**:
- Python (keyboard/pynput, pystray, PyInstaller) - mature library support, rapid development
- AutoHotkey - domain-specific but limited for file management features
- C# / .NET - overkill for a simple utility, complex keyboard hook implementation

**Rationale**: Python offers the best balance of rapid development, mature keyboard hooking libraries, and flexibility for the suggestion tracking/file management features. The ~20MB executable size is acceptable for a personal utility.

**Key Tradeoffs Accepted**:
- Larger executable size (~20MB vs ~2MB for AutoHotkey)
- Slightly slower startup than native solutions
- Possible antivirus false positives from PyInstaller

**Core Libraries**:
- `keyboard` or `pynput` - system-wide keystroke monitoring (to be evaluated)
- `pystray` - Windows system tray integration
- `PyInstaller` - single .exe packaging

---

### Decision 2: Development Environment
**Choice**: Develop directly on Windows machine, access remotely from Mac

**Date**: 2026-01-31

**Options Considered**:
- Develop on Windows directly (remote access from Mac) - can test keyboard hooks immediately
- Code on Mac, sync to Windows for testing - adds friction, can't test core functionality locally
- Windows VM on Mac - unnecessary given available Windows hardware

**Rationale**: The keyboard hook functionality is Windows-specific and untestable on Mac. Developing directly on Windows keeps the feedback loop tight - you can test immediately as you code.

**Key Tradeoffs Accepted**:
- Need to set up remote access (one-time setup)
- Development happens on Windows, not Mac

**Setup Required** (to be done in Phase 1):
- Enable Remote Desktop on Windows PC, OR
- Set up OpenSSH Server on Windows for VS Code Remote-SSH
- Configure from Mac to connect

---

### Decision 3: Testing Framework
**Choice**: pytest for unit/integration tests, Hypothesis for property-based tests

**Date**: 2026-01-31

**Options Considered**:
- pytest - simple, widely used, excellent plugin ecosystem
- unittest - built-in but more verbose, class-based syntax
- Hypothesis - standard for property-based testing in Python

**Rationale**: pytest is the modern Python testing standard with minimal boilerplate. Hypothesis integrates cleanly with pytest and enables the property-based tests outlined in the design document (casing preservation, log rotation limits, etc.).

**Key Tradeoffs Accepted**:
- Additional dependencies (pytest, hypothesis) vs built-in unittest

**Test Categories** (from design.md):
- Unit tests: rule parsing, casing logic, whole-word matching, log rotation
- Property-based tests: rule integrity, casing preservation, log size limits
- Integration tests: full correction flow, hotkey addition, suggestion lifecycle
- Manual testing: cross-application verification (Notepad, Chrome, VS Code, Word)

---

### Decision 4: Version Control & Distribution
**Choice**: GitHub for code backup and .exe distribution

**Date**: 2026-01-31

**Rationale**: GitHub provides free code backup, version history, and GitHub Releases for distributing the .exe to other Windows machines. No need for a separate installer or update mechanism - users can download the latest release manually.

**How it works**:
- Code lives in a GitHub repository
- When you build a new version, upload the .exe to GitHub Releases
- Other Windows PCs download the .exe from Releases (no git clone needed)

**Setup Required** (to be done in Phase 1):
- Create GitHub repository
- Set up git on Windows development machine
- (Optional) Create a simple build script that packages with PyInstaller

**Distribution Workflow**:
1. Make code changes
2. Run PyInstaller to create .exe
3. Create a new GitHub Release and upload the .exe
4. Other machines download from Releases page

---
