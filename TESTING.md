# Manual Testing Checklist

Use this checklist to verify Custom Autocorrect functionality before releases.

## Prerequisites

- [ ] Built executable exists: `dist/CustomAutocorrect.exe`
- [ ] Running on Windows 10 or Windows 11
- [ ] Running as Administrator (recommended)

---

## Core Functionality

### Correction Engine

- [ ] Type "teh " → corrected to "the "
- [ ] Type "adn " → corrected to "and "
- [ ] Type "TEH " → corrected to "THE " (uppercase preserved)
- [ ] Type "Teh " → corrected to "The " (capitalized preserved)
- [ ] Type "tEh " → corrected to "the " (mixed case → lowercase)
- [ ] Type "Teheran " → NOT corrected (whole word rule)
- [ ] Corrections happen silently (no popup, no sound)

### Rule Management

- [ ] rules.txt edits are detected automatically
- [ ] New rules work within 2 seconds of saving
- [ ] Invalid rules (no =) are skipped with warning on startup
- [ ] Comments (#) are ignored
- [ ] Blank lines are ignored
- [ ] Duplicate rules use the last definition

### Undo Support

- [ ] Type correction trigger → correction happens
- [ ] Press Ctrl+Z → original text restored
- [ ] Works in Notepad
- [ ] Works in Chrome text field
- [ ] Works in VS Code

---

## Password Protection

- [ ] Browser login form → corrections skipped
- [ ] Browser password field → corrections skipped
- [ ] Windows credential dialog → corrections skipped
- [ ] Chrome incognito mode → corrections work in non-password fields

---

## System Tray Integration

### Icon Appearance

- [ ] Pillow icon appears in system tray on startup
- [ ] Icon remains after sleep/wake cycle
- [ ] Tooltip shows "Custom Autocorrect" on hover

### Menu - View Suggestions

- [ ] Shows dialog with pending suggestions
- [ ] Shows "No suggestions yet" if empty
- [ ] Suggestion count updates in menu label

### Menu - Ignore Suggestion

- [ ] Shows list of suggestions to ignore
- [ ] Selecting and clicking "Ignore" adds to ignore.txt
- [ ] Ignored patterns no longer appear in suggestions

### Menu - Open Rules File

- [ ] Opens rules.txt in default editor
- [ ] Creates file if missing

### Menu - Open Corrections Log

- [ ] Opens corrections.log in default editor
- [ ] Creates file if missing

### Menu - Restore Rules Backup

- [ ] Only visible when backup exists
- [ ] Shows confirmation dialog with backup info
- [ ] Restores rules.txt from backup on confirm

### Menu - Start with Windows

- [ ] Shows checkbox state correctly
- [ ] Clicking toggles the checkbox
- [ ] Creates shortcut in Startup folder when enabled
- [ ] Removes shortcut when disabled
- [ ] App starts on Windows reboot when enabled

### Menu - Exit

- [ ] Cleanly stops the application
- [ ] Removes tray icon
- [ ] Shows correction statistics in console

---

## Hotkey (Win+Shift+A)

### Basic Functionality

- [ ] Win+Shift+A opens add rule dialog
- [ ] Dialog appears in foreground
- [ ] Can enter typo and correction
- [ ] New rule is saved to rules.txt
- [ ] New rule works immediately

### Edge Cases

- [ ] Empty typo rejected with error
- [ ] Empty correction rejected with error
- [ ] Typo = correction rejected with error
- [ ] Dialog can be cancelled with Escape or X

### Application Context

- [ ] Works from Notepad
- [ ] Works from Chrome
- [ ] Works from VS Code
- [ ] Works from desktop

---

## Pattern Detection

### Backspace-based Learning

- [ ] Type "hte", backspace 3 times, type "the" → pattern recorded
- [ ] Repeat 5 times → pattern appears in suggestions
- [ ] Different patterns tracked independently

### Ignore List

- [ ] Words in ignore.txt not suggested
- [ ] Custom words in custom-words.txt not suggested
- [ ] Dictionary words not suggested

---

## Startup & Lifecycle

### First Run Experience

- [ ] Creates Documents/CustomAutocorrect folder
- [ ] Creates sample rules.txt with examples
- [ ] Shows helpful startup message

### Single Instance

- [ ] Running second instance shows warning dialog
- [ ] Second instance exits cleanly
- [ ] Works when running from different directories

### Fallback Storage

- [ ] If Documents not writable → uses fallback location
- [ ] Shows note about fallback location on startup
- [ ] All features work with fallback location

### Clean Shutdown

- [ ] Ctrl+C stops application
- [ ] Exit from tray stops application
- [ ] Shows correction count on exit
- [ ] Shows pending suggestion count on exit

---

## Application Compatibility

Test in each of these applications:

### Notepad
- [ ] Corrections work
- [ ] Undo works
- [ ] No visible flicker during correction

### Chrome
- [ ] Corrections work in text fields
- [ ] Corrections work in address bar
- [ ] Undo works
- [ ] Password fields skipped

### VS Code
- [ ] Corrections work in editor
- [ ] Corrections work in search box
- [ ] Undo works

### Microsoft Word
- [ ] Corrections work
- [ ] Undo works
- [ ] No conflict with Word's autocorrect

### Windows Search
- [ ] Corrections work in Start menu search
- [ ] Corrections work in File Explorer search

---

## Performance

- [ ] Memory usage stays under 50 MB during normal use
- [ ] No noticeable input lag when typing
- [ ] App starts within 3 seconds
- [ ] Rules reload within 2 seconds of file change

---

## Error Handling

### Corrupt Rules File

- [ ] App starts even if rules.txt is corrupted
- [ ] Shows parse errors in console
- [ ] "Restore Rules Backup" available if backup exists

### Permission Issues

- [ ] Clear error message if can't access Documents
- [ ] Fallback to alternative location
- [ ] Clear error if keyboard hook fails

---

## Build Verification

After running `python build.py`:

- [ ] dist/CustomAutocorrect.exe created
- [ ] Executable size is 15-30 MB
- [ ] Runs on fresh Windows installation (no Python required)
- [ ] Icon displays correctly in File Explorer
- [ ] Icon displays correctly in system tray

---

## Version Checklist

Before creating a release:

- [ ] Version in `__init__.py` matches release version
- [ ] Version in `pyproject.toml` matches release version
- [ ] All tests pass: `pytest tests/`
- [ ] README.md is up to date
- [ ] TESTING.md checklist completed

---

## Notes

Record any issues found during testing:

| Test | Issue | Resolution |
|------|-------|------------|
|      |       |            |
|      |       |            |
|      |       |            |
